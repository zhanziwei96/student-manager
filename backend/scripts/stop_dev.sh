#!/bin/bash

# 班级管理系统 - 停止开发环境脚本

echo "=========================================="
echo "    班级管理系统 - 停止开发环境"
echo "=========================================="
echo ""

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# 停止后端
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        sleep 1
        echo "后端已停止"
    else
        echo "后端服务未运行"
    fi
    rm -f .backend.pid
else
    echo "未找到后端PID文件，尝试查找进程..."
    pkill -f "python.*backend/app.py" 2>/dev/null && echo "后端已停止" || echo "后端未运行"
fi

echo ""

# 停止前端
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        sleep 1
        echo "前端已停止"
    else
        echo "前端服务未运行"
    fi
    rm -f .frontend.pid
else
    echo "未找到前端PID文件，尝试查找进程..."
    pkill -f "vite" 2>/dev/null && echo "前端已停止" || echo "前端未运行"
fi

echo ""
echo "=========================================="
echo "  所有服务已停止"
echo "=========================================="
