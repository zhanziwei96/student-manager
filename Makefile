# 班级管理系统 Makefile
# 常用命令快捷方式

.PHONY: help install dev build deploy clean

help:
	@echo "班级管理系统 - 常用命令"
	@echo ""
	@echo "  make install    - 安装前端和后端依赖"
	@echo "  make dev        - 启动开发环境"
	@echo "  make build      - 构建生产环境前端"
	@echo "  make deploy     - 生产环境部署（需要 sudo）"
	@echo "  make clean      - 清理构建文件"
	@echo "  make update     - 更新代码并重新部署"

install:
	@echo "安装前端依赖..."
	cd frontend && npm install
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt

dev:
	@echo "启动开发环境..."
	@echo "请同时运行: make dev-backend 和 make dev-frontend"

dev-backend:
	cd backend && python app.py

dev-frontend:
	cd frontend && npm run dev

build:
	@echo "构建前端项目..."
	cd frontend && npm run build
	@echo "构建完成！文件位于 frontend/dist/"

deploy: build
	@echo "生产环境部署..."
	bash backend/scripts/deploy.sh

update:
	@echo "更新代码..."
	git pull
	@echo "重新构建..."
	cd frontend && npm install && npm run build
	@echo "重启服务..."
	sudo systemctl restart student-manage
	sudo systemctl restart nginx
	@echo "更新完成！"

clean:
	@echo "清理构建文件..."
	cd frontend && rm -rf dist node_modules
	cd backend && rm -rf venv __pycache__
	@echo "清理完成！"

# 生产环境快捷命令
start:
	sudo systemctl start student-manage nginx

stop:
	sudo systemctl stop student-manage nginx

restart:
	sudo systemctl restart student-manage nginx

status:
	sudo systemctl status student-manage nginx

logs:
	sudo journalctl -u student-manage -f
