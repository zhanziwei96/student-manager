# 快速部署指南

## 1. 环境检查

```bash
# 检查是否已部署
curl http://localhost:8000/health
curl http://localhost:3000
redis-cli ping

# 如果都正常，环境已就绪 ✅
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

# 启动
python main.py
```

### 2.2 前端
```bash
cd frontend
pnpm install
pnpm dev
```

### 2.3 Redis
```bash
# Ubuntu
sudo apt install redis-server
sudo systemctl start redis-server

# 验证
redis-cli ping  # 应返回 PONG
```

## 3. 一键启动

```bash
# 使用 Makefile
cd /home/yufeng/student-manager
make dev    # 启动所有服务
make stop   # 停止所有服务
make logs   # 查看日志
```

## 4. 验证部署

```bash
# 1. 健康检查
curl http://localhost:8000/health

# 2. 登录测试
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 3. 前端访问
open http://localhost:3000
```

## 5. 常见问题

### 端口冲突
```bash
lsof -i :8000  # 后端端口
lsof -i :3000  # 前端端口
lsof -i :6379  # Redis 端口
kill -9 <PID>
```

### 依赖重装
```bash
# 前端
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
| 前端 | http://localhost:3000 | 用户界面 |
| API 文档 | http://localhost:8000/docs | Swagger |
| Redis | localhost:6379 | 缓存/限流 |
| 数据库 | backend/data/*.db | SQLite |

---

详细配置见 [CONFIG_GUIDE.md](./CONFIG_GUIDE.md)
