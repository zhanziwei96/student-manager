# 快速部署指南

## 1. 环境检查

```bash
# 检查是否已部署
curl http://localhost:8000/api/health  # 后端
curl http://localhost:5173             # 前端 (frontend-v3)

# 如果正常返回，环境已就绪 ✅
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

## 3. 一键启动

```bash
# 使用 Makefile
cd /home/yufeng/student-manager

make dev-backend   # 终端1: 启动后端
make dev-frontend  # 终端2: 启动前端 (frontend-v3)

make stop          # 停止所有服务
make logs          # 查看日志
```

## 4. 验证部署

```bash
# 1. 健康检查
curl http://localhost:8000/api/health

# 2. 登录测试
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","role":"admin"}'

# 3. 前端访问
open http://localhost:5173
```

## 5. 常见问题

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

## 6. 环境信息

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 | http://localhost:8000 | API 服务 |
| 前端 | http://localhost:5173 | 用户界面 (frontend-v3) |
| API 文档 | http://localhost:8000/docs | Swagger |
| 数据库 | backend/data/class_system.db | SQLite |

**注意**: 
- 后端服务不依赖 Redis，限流使用内存存储
- 前端使用 Vite，默认端口 5173
- 前端代码位于 `frontend-v3/` 目录

---

详细配置见 [CONFIG_GUIDE.md](./CONFIG_GUIDE.md)
