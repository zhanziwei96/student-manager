#!/bin/bash

# 班级管理系统 - Linux停止脚本

echo "=========================================="
echo "    班级管理系统 - 停止服务"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 停止后端
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "[1/2] 停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        sleep 1
        echo "      已停止"
    else
        echo "[1/2] 后端服务未运行"
    fi
    rm -f .backend.pid
else
    # 尝试通过进程名停止
    pkill -f "python3 backend/app.py" 2>/dev/null && echo "[1/2] 停止后端服务" || echo "[1/2] 后端服务未运行"
fi

# 停止前端
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "[2/2] 停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        sleep 1
        echo "      已停止"
    else
        echo "[2/2] 前端服务未运行"
    fi
    rm -f .frontend.pid
else
    # 尝试通过进程名停止
    pkill -f "npm run dev" 2>/dev/null && echo "[2/2] 停止前端服务" || echo "[2/2] 前端服务未运行"
fi

echo ""
echo "=========================================="
echo "  服务已停止"
echo "=========================================="
