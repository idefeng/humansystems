import os
import re
from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI(title="HumanSystems Status API", description="MCP 兼容的状态上报服务")

LOG_FILE = "/Users/idefeng/DEV/humansystems/storage/life/daily_log.md"

def get_latest_status():
    if not os.path.exists(LOG_FILE):
        return None, None

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 匹配最近的一个记录块
        # 记录块通常以 ## YYYY-MM-DD HH:MM:SS 开头
        entries = re.split(r'## \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', content)
        if len(entries) < 2:
            return None, None
        
        last_entry = entries[-1]
        
        # 提取“心情”和“核心事件”
        mood_match = re.search(r'[-*]\s*心情[：:]\s*(.*)', last_entry)
        task_match = re.search(r'[-*]\s*核心事件[：:]\s*(.*)', last_entry)
        
        mood = mood_match.group(1).strip() if mood_match else "未知"
        task = task_match.group(1).strip() if task_match else "无特定任务"
        
        return mood, task
    except Exception as e:
        print(f"解析日志失败: {e}")
        return None, None

@app.get("/status")
async def read_status():
    """
    读取最新的情绪和专注任务
    """
    mood, task = get_latest_status()
    
    if mood is None:
        raise HTTPException(status_code=404, detail="尚未生成任何日志记录")
    
    return {
        "emotion": mood,
        "current_task": task,
        "source": "storage/life/daily_log.md"
    }

if __name__ == "__main__":
    # 默认运行在 8000 端口
    uvicorn.run(app, host="0.0.0.0", port=8000)
