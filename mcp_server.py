from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import pandas as pd
import json
import os
import uvicorn
import time

app = FastAPI(title="HumanSystems Core API")
PROTECTION_MODE = False

# 启用 CORS 以支持 Stitch 仪表盘跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

JSONL_DATABASE = "/Users/idefeng/DEV/humansystems/storage/life/database.jsonl"

def load_data():
    """高效加载 JSONL 数据并转化为 DataFrame"""
    if not os.path.exists(JSONL_DATABASE):
        return pd.DataFrame()
    
    try:
        with open(JSONL_DATABASE, 'r', encoding='utf-8') as f:
            data = [json.loads(line) for line in f if line.strip()]
        
        df = pd.DataFrame(data)
        if not df.empty:
            # 使用 apply(pd.to_datetime, utc=True) 逐行处理混合时区问题
            df['timestamp'] = df['timestamp'].apply(lambda x: pd.to_datetime(x, utc=True))
            # 移除解析失败的行并排序
            df = df.dropna(subset=['timestamp']).sort_values('timestamp')
        return df
    except Exception as e:
        print(f"数据加载失败: {e}")
        return pd.DataFrame()

@app.get("/mood/history")
def get_mood_history(days: int = 7):
    """
    获取过去 N 天的情绪曲线数据
    """
    df = load_data()
    if df.empty:
        return []
    
    cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=days)
    # 确保时区一致
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    mask = df['timestamp'] > cutoff
    history = df.loc[mask].copy()
    
    history['timestamp'] = history['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # 提取 fatigue_score，如果不存在于 metadata 则默认为 0.0
    def extract_fatigue(row):
        if 'metadata' in row and isinstance(row['metadata'], dict):
            return row['metadata'].get('fatigue_score', 0.0)
        return 0.0

    history['fatigue_score'] = history.apply(extract_fatigue, axis=1)
    
    return history[['timestamp', 'sentiment', 'category', 'fatigue_score', 'content']].to_dict(orient='records')

@app.get("/stats/summary")
def get_life_stats():
    """
    生命统计摘要
    """
    df = load_data()
    if df.empty:
        return {"message": "No data"}

    week_mask = pd.to_datetime(df['timestamp'], utc=True) > (pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=7))
    this_week = df.loc[week_mask]

    if this_week.empty:
        return {"message": "本周暂无数据"}

    return {
        "avg_sentiment": round(float(this_week['sentiment'].mean()), 2),
        "total_events": len(this_week),
        "category_dist": this_week['category'].value_counts().to_dict(),
        "action_items_count": int(this_week['action_item'].sum())
    }

@app.get("/events/search")
def search_events(q: Optional[str] = None, category: Optional[str] = None, limit: int = 20):
    """
    搜索历史事件
    """
    df = load_data()
    if df.empty:
        return []

    result = df
    if category:
        result = result[result['category'] == category]
    if q:
        result = result[result['content'].str.contains(q, case=False, na=False)]
    
    res = result.tail(limit).copy()
    res['timestamp'] = res['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    return res.to_dict(orient='records')

@app.post("/system/protection")
async def set_protection_mode(status: bool):
    """
    开启或关闭保护模式
    """
    global PROTECTION_MODE
    PROTECTION_MODE = status
    return {"status": "success", "protection_mode": PROTECTION_MODE}

@app.get("/status")
def get_status():
    """
    获取系统状态，包含语音助手在线状态及保护模式状态
    """
    df = load_data()
    if df.empty:
        return {"status": "inactive", "recent_history": [], "assistant_online": False, "protection_mode": PROTECTION_MODE}
    
    # 确保时区一致并按时间排序
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    
    # 检查语音助手在线状态 (10分钟内是否有 mac-voice-assistant 的数据)
    ten_minutes_ago = pd.Timestamp.now(tz='UTC') - pd.Timedelta(minutes=10)
    assistant_online = False
    
    # 获取含有 metadata 且 source 为 mac-voice-assistant 的记录
    def check_source(m):
        if isinstance(m, dict):
            return m.get("source") == "mac-voice-assistant"
        return False

    if 'metadata' in df.columns:
        recent_assistant_data = df[
            (df['metadata'].apply(check_source)) & 
            (df['timestamp'] > ten_minutes_ago)
        ]
        assistant_online = not recent_assistant_data.empty

    history = df.sort_values('timestamp').tail(20).copy()
    history['timestamp'] = history['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # 修复 JSON 序列化 NaN 导致的 500 错误
    history = history.where(pd.notnull(history), None)
    
    avg_sentiment = round(float(history['sentiment'].tail(5).mean()), 2) if not history.empty else 0.5
    
    return {
        "status": "active",
        "assistant_online": assistant_online,
        "protection_mode": PROTECTION_MODE,
        "recent_history": history.to_dict(orient='records'),
        "mood_pulse": {
            "current_index": avg_sentiment,
            "label": "Stable" if 0.4 <= avg_sentiment <= 0.7 else "Volatile"
        }
    }

@app.post("/events/record")
async def record_event(event: dict):
    """
    记录来自语音助手的事件
    """
    content = event.get("content", "")
    fatigue_score = event.get("fatigue_score", 0.0)
    sentiment = event.get("sentiment", 0.5)
    
    new_event = {
        "timestamp": pd.Timestamp.now(tz='UTC').isoformat(),
        "content": content,
        "sentiment": sentiment,
        "category": "voice_interaction",
        "action_item": False,
        "metadata": {
            "source": "nexus-voice-assistant",
            "fatigue_score": fatigue_score
        }
    }
    
    try:
        with open(JSONL_DATABASE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(new_event, ensure_ascii=False) + "\n")
        return {"status": "success", "message": "Event recorded"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/events/ingest")
async def ingest_event(payload: dict):
    """
    标准化入库接口，支持对齐 watcher.py 结构
    接收: text, fatigue_score, source
    """
    try:
        # 兼容旧版本发出的 final_text 字段
        text = payload.get("text") or payload.get("final_text") or ""
        fatigue_score = float(payload.get("fatigue_score", 0.0))
        source = payload.get("source", "unknown")
        
        # 自动补齐：如果 source 为未知但有内容，假设来自语音助手
        if source == "unknown" and text:
            source = "mac-voice-assistant"
        
        # 对齐 watcher.py 的结构要求
        # 疲劳值较高（>0.4）归为健康类，否则为生活类
        category = "健康" if fatigue_score > 0.4 else "生活"
        # 情绪分值与疲劳值反向关联 (1.0 - 疲劳值)
        sentiment = round(max(0.0, min(1.0, 1.0 - fatigue_score)), 2)
        
        new_event = {
            "timestamp": pd.Timestamp.now(tz='UTC').isoformat(),
            "category": category,
            "content": text,
            "action_item": False,
            "sentiment": sentiment,
            "metadata": {
                "source": source,
                "fatigue_score": fatigue_score,
                "ingest_type": "api"
            }
        }
        
        with open(JSONL_DATABASE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(new_event, ensure_ascii=False) + "\n")
            
        return {"status": "success", "message": "Data ingested successfully"}
    except Exception as e:
        print(f"Ingest failed: {e}")
        return {"status": "error", "message": f"Server side error: {str(e)}"}

if __name__ == "__main__":
    # 使用 8000 端口，确保与 Stitch 默认配置一致
    uvicorn.run(app, host="0.0.0.0", port=8000)
