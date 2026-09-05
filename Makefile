# 班级管理系统 Makefile
# 常用命令快捷方式

.PHONY: help install dev dev-backend dev-frontend stop logs status test test-backend test-frontend type-check clean

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
	@echo "  make test           - 运行所有测试"
	@echo "  make test-backend   - 仅运行后端测试"
	@echo "  make test-frontend  - 仅运行前端测试"
	@echo "  make type-check     - 前端 TypeScript 类型检查"
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

# 启动后端服务（需要 conda 环境，开发模式热重载）
dev-backend:
	@echo "启动后端服务（开发模式，热重载）..."
	cd backend && conda run -n student-manage ENV=development python main.py

# 启动前端服务
dev-frontend:
	@echo "启动前端服务 (frontend-v3)..."
	cd frontend-v3 && pnpm dev

# 后台启动后端（用于脚本/CI）
dev-backend-bg:
	@echo "后台启动后端服务..."
	cd backend && nohup conda run -n student-manage ENV=development python main.py > logs/dev-backend.log 2>&1 &
	@sleep 5
	@curl -s --max-time 5 http://localhost:8000/api/v1/health && echo " ✅ 后端启动成功" || echo " ❌ 后端启动失败"

# 后台启动前端（用于脚本/CI）
dev-frontend-bg:
	@echo "后台启动前端服务..."
	cd frontend-v3 && nohup pnpm dev > ../logs/dev-frontend.log 2>&1 &
	@sleep 3
	@curl -s --max-time 5 http://localhost:5173 > /dev/null && echo " ✅ 前端启动成功" || echo " ❌ 前端启动失败"

# 停止服务（根据进程名查找并停止，含残留检查）
stop:
	@echo "停止后端服务..."
	-pkill -f "python main.py" 2>/dev/null || true
	@sleep 3
	@ps aux | grep "python.*main.py" | grep -v grep && (echo "发现残留进程，强制结束..." && pkill -9 -f "python.*main.py") || true
	@echo "停止前端服务..."
	-pkill -f "vite" 2>/dev/null || pkill -f "pnpm dev" 2>/dev/null || true
	@sleep 2
	@ps aux | grep -E "vite|pnpm.*dev" | grep -v grep && (echo "发现残留进程，强制结束..." && pkill -9 -f "vite" && pkill -9 -f "pnpm.*dev") || true
	@echo "服务已停止"

# 查看日志（使用 tail 查看最新日志）
logs:
	@echo "=== 后端日志 (production.log) ==="
	@tail -20 backend/logs/production.log 2>/dev/null || echo "暂无生产日志"
	@echo ""
	@echo "=== 后端日志 (app.log) ==="
	@tail -20 backend/logs/app.log 2>/dev/null || echo "暂无应用日志"
	@echo ""
	@echo "=== 前端日志 ==="
	@echo "前端日志输出在终端，请查看运行 frontend-v3 的终端窗口"

# 检查服务状态
status:
	@echo "=== 后端状态 ==="
	@curl -s --max-time 3 http://localhost:8000/api/v1/health 2>/dev/null && echo " ✅ 后端运行中" || echo " ❌ 后端未运行"
	@echo ""
	@echo "=== 前端状态 (frontend-v3) ==="
	@curl -s --max-time 3 http://localhost:5173 2>/dev/null >/dev/null && echo " ✅ 前端运行中" || echo " ❌ 前端未运行"

# 运行所有测试
test: test-backend test-frontend

# 运行后端测试
test-backend:
	@echo "=== 运行后端测试 ==="
	conda run -n student-manage pytest tests/ -v

# 运行前端测试
test-frontend:
	@echo "=== 运行前端测试 ==="
	cd frontend-v3 && pnpm test:run

# 前端 TypeScript 类型检查
type-check:
	@echo "=== 前端类型检查 ==="
	cd frontend-v3 && pnpm vue-tsc --noEmit

# 清理构建文件
clean:
	@echo "清理构建文件..."
	cd frontend-v3 && rm -rf dist node_modules
	cd backend && rm -rf __pycache__ *.pyc logs/*.log
	@echo "清理完成！"
