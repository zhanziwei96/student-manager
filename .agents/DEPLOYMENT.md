# 快速部署指南

---

**文档版本**: v2.0  
**最后更新**: 2026-04-03  
**适用版本**: v3.0.0+  
**状态**: ✅ 已同步代码

---

> **最后更新时间**: 2026-03-27

## 1. 环境检查

部署前**必须**检查服务状态，避免重复部署：

```bash
# 检查后端是否已运行
curl -s http://localhost:8000/api/v1/health && echo "后端运行中 ✅"

# 检查前端是否已运行
curl -s http://localhost:5173 > /dev/null && echo "前端运行中 ✅"

# 如果都正常返回，环境已就绪，无需重新部署
```

## 2. 首次部署

### 2.1 后端

```bash
cd backend

# 创建环境
conda create -n student-manage python=3.11 -y
conda activate student-manage

# 安装依赖
pip install -r requirements.txt

# 启动（生产环境）
ENV=production python main.py
```

### 2.2 前端 (frontend-v3)

```bash
cd frontend-v3
pnpm install
pnpm dev
```

## 3. 服务重启流程（强制）

**⚠️ 警告**: 禁止直接执行 `python main.py` 或 `pnpm dev`，必须按以下流程操作。

### 后端重启

```bash
# 1. 停止现有服务
pkill -f "python main.py" 2>/dev/null || true
sleep 3  # 必须等待！

# 2. 检查残留进程
ps aux | grep "python.*main.py" | grep -v grep

# 3. 启动新服务
cd /home/yufeng/student-manager/backend
conda run -n student-manage ENV=production python main.py &
sleep 5

# 4. 验证启动
curl -s http://localhost:8000/api/v1/health  # 必须验证！
```

### 前端重启

```bash
# 1. 停止现有服务
pkill -f "pnpm dev" 2>/dev/null || true
sleep 2

# 2. 启动新服务
cd /home/yufeng/student-manager/frontend-v3
pnpm dev &
sleep 3

# 3. 验证启动
curl -s http://localhost:5173 > /dev/null && echo "前端运行中 ✅"
```

## 4. 一键启动（Makefile）

```bash
cd /home/yufeng/student-manager

# 检查状态
make status

# 启动服务（开两个终端）
make dev-backend   # 终端1: 启动后端
make dev-frontend  # 终端2: 启动前端 (frontend-v3)

# 停止服务
make stop

# 查看日志
make logs
```

## 5. 验证部署

```bash
# 1. 健康检查
curl http://localhost:8000/api/v1/health

# 2. 登录测试
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","role":"admin"}'

# 3. 前端访问
open http://localhost:5173
```

## 6. 常见问题

### 端口冲突

```bash
lsof -i :8000   # 后端端口
lsof -i :5173   # 前端端口 (frontend-v3)
kill -9 <PID>
```

### 依赖重装

```bash
# 前端 (frontend-v3)
cd frontend-v3
rm -rf node_modules pnpm-lock.yaml
pnpm install

# 后端
pip cache purge
pip install -r requirements.txt --force-reinstall
```

### Conda 环境

```bash
# 如果激活失败
source /home/yufeng/miniconda3/bin/activate student-manage
```

## 7. 环境信息

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 | http://localhost:8000 | API 服务 |
| 前端 | http://localhost:5173 | 用户界面 (frontend-v3) |
| API 文档 | http://localhost:8000/docs | Swagger |
| 数据库 | backend/app/data/class_system.db | SQLite |

**注意**: 
- 后端服务不依赖 Redis，限流使用内存存储
- 前端使用 Vite，默认端口 5173
- 前端代码位于 `frontend-v3/` 目录

## 8. 架构约束（2026-03-27更新）

### 8.1 部署禁令

| # | 禁令 | 违反后果 |
|---|------|----------|
| 1 | ❌ 不要在未检查服务状态的情况下重启服务 | 重复部署，端口冲突 |
| 2 | ❌ 不要快速连续执行停止+启动命令 | 残留进程导致启动失败 |
| 3 | ❌ 不要假设数据库/服务路径 | 操作错误的文件 |
| 4 | ❌ 不要在未验证的情况下认为操作成功 | 隐藏错误 |

### 8.2 环境要求

| 依赖 | 版本 | 检查命令 |
|------|------|----------|
| Python | 3.11+ | `python --version` |
| Conda | 最新 | `conda --version` |
| Node.js | 20+ | `node --version` |
| pnpm | 8+ | `pnpm --version` |

**必须激活虚拟环境**: `conda activate student-manage`

### 8.3 检查清单

部署前必须执行：

```bash
# 1. 环境检查 (必须)
which python  # 确认是 miniconda 路径

# 2. 服务状态检查 (必须)
curl -s http://localhost:8000/api/v1/health  # 后端是否已运行？
curl -s http://localhost:5173 > /dev/null && echo "前端运行中"  # 前端是否已运行？

# 3. 数据库路径确认 (涉及 DB 操作时必须)
python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"
```

**决策逻辑**: 服务已运行 → 不需要重启；服务未运行 → 按重启流程执行

## 9. Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

详细配置见 [CONFIG_GUIDE.md](./CONFIG_GUIDE.md)

**文档版本**: v2.0  
**最后更新**: 2026-03-27（新增服务重启强制流程和架构约束）
