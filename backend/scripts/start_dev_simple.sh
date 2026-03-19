#!/bin/bash

# 班级管理系统 - Linux简单启动脚本（使用后台进程）

echo "=========================================="
echo "    班级管理系统 - 开发环境启动"
echo "=========================================="
echo ""

# 获取项目根目录（脚本在 backend/scripts/ 下）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# 启动后端
echo "[1/2] 启动后端服务..."
nohup python3 backend/app.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "      后端PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 启动前端
echo "[2/2] 启动前端服务..."
cd frontend
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "      前端PID: $FRONTEND_PID"

# 保存PID到文件
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo ""
echo "=========================================="
echo "  服务启动成功！"
echo "=========================================="
echo ""
echo "  后端: http://localhost:5000"
echo "  前端: http://localhost:3000"
echo ""
echo "  默认账号: admin / admin123"
echo ""
echo "=========================================="
echo ""
echo "使用 ./backend/scripts/stop_dev.sh 停止服务"
echo "查看日志: tail -f backend.log 或 tail -f frontend.log"
echo ""
