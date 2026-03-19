#!/bin/bash
# DDD架构后端启动脚本

cd "$(dirname "$0")"

# 生成或加载 SECRET_KEY
if [ -f .env ]; then
    export $(cat .env | xargs)
else
    export SECRET_KEY=$(openssl rand -hex 32)
    echo "SECRET_KEY=$SECRET_KEY" > .env
    echo "✅ 已生成新的 SECRET_KEY"
fi

echo "🚀 启动 DDD架构后端服务..."
echo "📍 后端地址: http://localhost:5000"
echo "📍 API文档: http://localhost:5000/"
echo ""

python main.py
