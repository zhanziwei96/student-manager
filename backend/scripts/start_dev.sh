#!/bin/bash

# 班级管理系统 - Linux开发环境一键启动脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}    班级管理系统 - 开发环境启动脚本${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# 获取项目根目录（脚本在 backend/scripts/ 下）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# 检查后端依赖
echo -e "${YELLOW}[检查] 检查Python依赖...${NC}"
if ! python3 -c "import flask, flask_cors" 2>/dev/null; then
    echo -e "${YELLOW}[安装] 正在安装Python依赖...${NC}"
    cd backend
    pip3 install -r requirements.txt
    cd ..
fi

# 检查前端依赖
echo -e "${YELLOW}[检查] 检查Node依赖...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}[安装] 正在安装Node依赖...${NC}"
    cd frontend
    npm install
    cd ..
fi

echo ""
echo -e "${GREEN}[启动] 正在启动服务...${NC}"
echo ""

# 启动后端
echo -e "${BLUE}[1/2] 启动后端服务 (Flask)...${NC}"
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
echo -e "${YELLOW}      等待后端启动 (3秒)...${NC}"
sleep 3

# 检查后端是否启动成功
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}[错误] 后端启动失败${NC}"
    exit 1
fi

echo -e "${GREEN}      后端已启动 (PID: $BACKEND_PID)${NC}"
echo ""

# 启动前端
echo -e "${BLUE}[2/2] 启动前端服务 (Vue)...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# 等待前端启动
echo -e "${YELLOW}      等待前端启动 (5秒)...${NC}"
sleep 5

# 检查前端是否启动成功
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}[错误] 前端启动失败${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}      前端已启动 (PID: $FRONTEND_PID)${NC}"
echo ""

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  服务启动成功！${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "  ${BLUE}后端地址:${NC} http://localhost:5000"
echo -e "  ${BLUE}前端地址:${NC} http://localhost:3000"
echo -e "  ${BLUE}管理后台:${NC} http://localhost:3000/admin"
echo -e "  ${BLUE}签到页面:${NC} http://localhost:3000/checkin"
echo ""
echo -e "  ${YELLOW}默认账号:${NC} admin / admin123"
echo ""
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "${YELLOW}提示: 按 Ctrl+C 停止所有服务${NC}"
echo ""

# 定义清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}[停止] 正在停止服务...${NC}"
    kill $FRONTEND_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 保持脚本运行
wait
