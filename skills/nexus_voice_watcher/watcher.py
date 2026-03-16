import os
import time
import json
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from volcenginesdkarkruntime import Ark
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 配置
WATCH_DIRECTORY = os.path.expanduser("~/nexus-voice/output")
JSONL_DATABASE = "/Users/idefeng/DEV/humansystems/storage/life/database.jsonl"
SUMMARY_FILE = "/Users/idefeng/DEV/humansystems/storage/life/daily_summary.md"
API_KEY = os.getenv("ARK_API_KEY")
ENDPOINT_ID = os.getenv("ARK_ENDPOINT_ID")

# 日志设置
os.makedirs("/Users/idefeng/DEV/humansystems/storage/logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/Users/idefeng/DEV/humansystems/storage/logs/watcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NexusVoiceHandler(FileSystemEventHandler):
    def __init__(self, ark_client):
        self.ark_client = ark_client

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            logger.info(f"检测到新文件: {event.src_path}")
            # 等待文件写入完成
            time.sleep(1)
            self.process_file(event.src_path)

    def process_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                return

            # 本地简单脱敏 (按 rules.md 要求)
            safe_content = content.replace("身份证", "[ID]").replace("密码", "[PWD]")

            # 调用火山引擎提取结构化 JSON
            record = self.extract_structured_json(safe_content)
            if not record:
                return

            # 1. 存入 JSONL
            self.append_to_jsonl(record)
            
            # 2. 存入 Markdown 摘要
            self.append_to_summary(record)
            
            logger.info(f"成功处理并存档记录: {record.get('category')}")

        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")

    def extract_structured_json(self, text):
        prompt = f"""
        请将以下文本转化为结构化 JSON。
        字段包含：
        - timestamp: 当前ISO时间字符串
        - category: 必须从 [工作, 生活, 健康, 灵感] 中选一个
        - content: 简写的内容摘要
        - action_item: 布尔值，是否有待办事项
        - sentiment: 情绪指数，0 到 1 之间的浮点数 (1代表极其积极)

        如果是“健康”类别，请特别注意是否存在生理指标异常。

        文本内容：
        {text}

        只返回纯 JSON，不要带 markdown 代码块。
        """

        try:
            completion = self.ark_client.chat.completions.create(
                model=ENDPOINT_ID,
                messages=[
                    {"role": "system", "content": "你是一个精确的结构化数据提取器。"},
                    {"role": "user", "content": prompt},
                ],
            )
            raw_json = completion.choices[0].message.content.strip()
            # 兼容带 Markdown 块的情况
            if raw_json.startswith("```"):
                raw_json = re.sub(r"```json|```", "", raw_json).strip()
            return json.loads(raw_json)
        except Exception as e:
            logger.error(f"AI 提取失败: {e}")
            return None

    def append_to_jsonl(self, record):
        os.makedirs(os.path.dirname(JSONL_DATABASE), exist_ok=True)
        with open(JSONL_DATABASE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def append_to_summary(self, record):
        os.makedirs(os.path.dirname(SUMMARY_FILE), exist_ok=True)
        
        timestamp = record.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%S"))
        category = record.get("category", "生活")
        content = record.get("content", "")
        sentiment = record.get("sentiment", 0.5)
        has_action = " [?] 待办" if record.get("action_item") else ""
        
        # 情绪表情映射
        mood_icon = "?" if sentiment > 0.8 else "?" if sentiment > 0.4 else "?"
        
        # 健康预警逻辑 (基于 rules.md)
        alert_msg = ""
        if category == "健康" and sentiment < 0.3:
            alert_msg = "\n> [!WARNING]\n> 检测到极端生理/情绪波动，触发健康风险预警（Rules.md 章节 6）。"

        entry = f"### [{category}] {timestamp} {mood_icon}\n- **内容**: {content}{has_action}\n- **情绪指数**: {sentiment}{alert_msg}\n\n"
        
        with open(SUMMARY_FILE, 'a', encoding='utf-8') as f:
            f.write(entry)

if __name__ == "__main__":
    import re
    if not os.path.exists(WATCH_DIRECTORY):
        os.makedirs(WATCH_DIRECTORY, exist_ok=True)

    client = Ark(api_key=API_KEY)
    event_handler = NexusVoiceHandler(client)
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
    
    logger.info(f"正在监控流程: {WATCH_DIRECTORY}")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
