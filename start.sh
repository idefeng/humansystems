#!/bin/bash

# 人生系统 (HumanSystems) 手动启动脚本

# 获取当前脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "正在启动人生系统..."

# 1. 启动 MCP 网关 (端口 8001)
echo "启动 MCP 网关 (Port 8001)..."
nohup python3 protocols/mcp_gateway.py > storage/logs/gateway.log 2>&1 &
echo $! > gateway.pid

# 2. 启动 语音监听器
echo "启动 语音监听器 (Watcher)..."
nohup python3 skills/nexus_voice_watcher/watcher.py > storage/logs/watcher.log 2>&1 &
echo $! > watcher.pid

echo "服务已在后台启动。"
echo "- MCP 网关日志: storage/logs/gateway.log"
echo "- 语音监听日志: storage/logs/watcher.log"
echo "--------------------------------------"
ps -p $(cat gateway.pid) $(cat watcher.pid)
