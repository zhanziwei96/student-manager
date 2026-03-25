#!/bin/bash
set -e

echo "=== Starting ClassHub ==="

# 创建必要的目录（确保挂载卷存在）
mkdir -p /app/backend/data /app/uploads /app/backups /app/backend/logs

# 检查数据库文件是否存在，如果不存在初始化
cd /app/backend

# 启动 FastAPI 后端（Uvicorn）
echo "[1/2] Starting FastAPI backend on port 8000..."
cd /app/backend
python -c "from app.core.db import init_db; init_db()" 2>/dev/null || echo "Database already initialized or init not needed"

# 使用 uvicorn 启动
uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2 --access-log --error-log &
UVICORN_PID=$!

# 等待后端启动
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    sleep 1
done

# 检查后端是否启动成功
if ! curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "Warning: Backend may not be ready yet, continuing anyway..."
fi

# 启动 Nginx
echo "[2/2] Starting Nginx on port 80..."
nginx -g 'daemon off;'
