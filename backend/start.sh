#!/bin/bash
# FastAPI 后端启动脚本

cd "$(dirname "$0")"

# 检查虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 生成 SECRET_KEY（如果不存在）
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
fi

echo "🚀 启动 FastAPI 后端服务..."
echo "📍 后端地址: http://localhost:8000"
echo "📍 API文档:  http://localhost:8000/docs"
echo "📍 Redoc:    http://localhost:8000/redoc"
echo ""

# 使用 uvicorn 启动
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
