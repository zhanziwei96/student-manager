# 班级管理系统 Makefile
# 常用命令快捷方式

.PHONY: help install dev dev-backend dev-frontend stop logs status

help:
	@echo "班级管理系统 - 常用命令"
	@echo ""
	@echo "  make install        - 安装前端和后端依赖（首次部署）"
	@echo "  make dev            - 启动所有开发服务"
	@echo "  make dev-backend    - 仅启动后端服务"
	@echo "  make dev-frontend   - 仅启动前端服务"
	@echo "  make stop           - 停止所有服务"
	@echo "  make logs           - 查看服务日志"
	@echo "  make status         - 检查服务状态"
	@echo "  make clean          - 清理构建文件"

# 首次部署 - 安装依赖
install:
	@echo "=== 安装后端依赖 ==="
	cd backend && pip install -r requirements.txt
	@echo "=== 安装前端依赖 (frontend-v3) ==="
	cd frontend-v3 && pnpm install
	@echo "=== 依赖安装完成 ==="

# 启动所有开发服务（需要多个终端或使用后台任务）
dev:
	@echo "启动开发环境..."
	@echo "建议开两个终端分别运行: make dev-backend 和 make dev-frontend"

# 启动后端服务（需要 conda 环境）
dev-backend:
	@echo "启动后端服务..."
	cd backend && conda run -n student-manage python main.py

# 启动前端服务
dev-frontend:
	@echo "启动前端服务 (frontend-v3)..."
	cd frontend-v3 && pnpm dev

# 停止服务（根据进程名查找并停止）
stop:
	@echo "停止后端服务..."
	-pkill -f "python main.py" 2>/dev/null || true
	@echo "停止前端服务..."
	-pkill -f "pnpm dev" 2>/dev/null || true
	@echo "服务已停止"

# 查看日志（使用 tail 查看最新日志）
logs:
	@echo "=== 后端日志 ==="
	tail -20 backend/logs/*.log 2>/dev/null || echo "暂无后端日志"
	@echo ""
	@echo "=== 前端日志 ==="
	@echo "前端日志输出在终端，请查看运行 frontend-v3 的终端窗口"

# 检查服务状态
status:
	@echo "=== 后端状态 ==="
	@curl -s http://localhost:8000/api/v1/health 2>/dev/null && echo " ✅ 后端运行中" || echo " ❌ 后端未运行"
	@echo ""
	@echo "=== 前端状态 (frontend-v3) ==="
	@curl -s http://localhost:5173 2>/dev/null >/dev/null && echo " ✅ 前端运行中" || echo " ❌ 前端未运行"

# 清理构建文件
clean:
	@echo "清理构建文件..."
	cd frontend-v3 && rm -rf dist node_modules
	cd backend && rm -rf __pycache__ *.pyc logs/*.log
	@echo "清理完成！"
