from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import pandas as pd
import json
import os
import uvicorn
import time

app = FastAPI(title="HumanSystems Core API")

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
    return history[['timestamp', 'sentiment', 'category']].to_dict(orient='records')

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

@app.get("/status")
def get_status():
    """
    兼容性接口：供 Stitch 仪表盘初始设计使用
    """
    df = load_data()
    if df.empty:
        return {"status": "inactive", "recent_history": []}
    
    history = df.tail(20).copy()
    history['timestamp'] = history['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    avg_sentiment = round(float(history['sentiment'].tail(5).mean()), 2) if not history.empty else 0.5
    
    return {
        "status": "active",
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

if __name__ == "__main__":
    # 使用 8000 端口，确保与 Stitch 默认配置一致
    uvicorn.run(app, host="0.0.0.0", port=8000)
