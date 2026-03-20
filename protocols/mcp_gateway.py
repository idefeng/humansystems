import os
import json
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="HumanSystems MCP Gateway", description="标准化的人生系统 MCP 接口网关")

JSONL_DATABASE = "/Users/idefeng/DEV/humansystems/storage/life/database.jsonl"

class ContextInjection(BaseModel):
    category: str = "外部注入"
    content: str
    action_item: bool = False
    sentiment: float = 0.5
    source_agent: Optional[str] = "unknown"

class MoodResponse(BaseModel):
    timestamp: str
    sentiment: float
    category: str
    content: str

class TaskResponse(BaseModel):
    timestamp: str
    category: str
    content: str
    sentiment: float

def read_database() -> List[dict]:
    if not os.path.exists(JSONL_DATABASE):
        return []
    records = []
    try:
        with open(JSONL_DATABASE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    except Exception as e:
        print(f"读取数据库失败: {e}")
    return records

@app.get("/latest_mood", response_model=MoodResponse)
async def get_latest_mood():
    """
    读取最近一次的心情指数
    """
    records = read_database()
    if not records:
        raise HTTPException(status_code=404, detail="尚无数据库记录")
    
    # 返回最后一条记录
    last_record = records[-1]
    return MoodResponse(
        timestamp=last_record.get("timestamp", ""),
        sentiment=last_record.get("sentiment", 0.5),
        category=last_record.get("category", "未知"),
        content=last_record.get("content", "")
    )

@app.get("/active_tasks", response_model=List[TaskResponse])
async def get_active_tasks():
    """
    扫描所有 action_item 为 true 的记录
    """
    records = read_database()
    active_tasks = [
        TaskResponse(
            timestamp=r.get("timestamp", ""),
            category=r.get("category", "未知"),
            content=r.get("content", ""),
            sentiment=r.get("sentiment", 0.5)
        )
        for r in records if r.get("action_item") is True
    ]
    return active_tasks

@app.post("/inject_context")
async def inject_context(data: ContextInjection):
    """
    允许 OpenClaw 将其他 Agent 的结论反馈回人生系统
    """
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "category": data.category,
        "content": f"[{data.source_agent}] {data.content}",
        "action_item": data.action_item,
        "sentiment": data.sentiment
    }
    
    try:
        os.makedirs(os.path.dirname(JSONL_DATABASE), exist_ok=True)
        with open(JSONL_DATABASE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return {"status": "success", "message": "上下文已成功注入"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注入失败: {e}")

if __name__ == "__main__":
    # 默认 8000 端口可能被占用，此处修改为 8001
    uvicorn.run(app, host="0.0.0.0", port=8001)
