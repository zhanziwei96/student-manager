#!/bin/bash
set -e

echo "=== Starting Student Manage v3 ==="

# 创建必要的目录
mkdir -p /app/backend/data /app/uploads /app/backups

# 启动 Flask 后端（Gunicorn）
echo "[1/2] Starting Flask backend on port 5000..."
cd /app
gunicorn -w 2 -b 127.0.0.1:5000 --access-logfile - --error-logfile - --daemon app:app

# 等待后端启动
sleep 2

# 检查后端是否启动成功
if ! curl -s http://127.0.0.1:5000/api/stats > /dev/null; then
    echo "Warning: Backend may not be ready yet, continuing anyway..."
fi

# 启动 Nginx
echo "[2/2] Starting Nginx on ports 80 and 443..."
nginx -g 'daemon off;'
