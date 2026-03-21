# ClassHub 环境部署文档

**版本**: v1.0  
**日期**: 2025-03-21  

---

## 快速开始

如果你看到此文档，说明项目环境可能已部署。请先检查以下服务状态：

```bash
# 检查后端服务
curl http://localhost:8000/health

# 检查前端服务
curl http://localhost:3000

# 检查 Redis
redis-cli ping
```

如果以上都正常返回，则**环境已就绪，无需重复部署**。

---

## 1. 环境要求

### 1.1 系统要求
| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Linux/macOS/Windows WSL | Ubuntu 22.04 LTS |
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 10GB SSD | 50GB+ SSD |
| 网络 | 能访问互联网 | 稳定网络 |

### 1.2 软件依赖
| 软件 | 版本要求 | 安装命令 |
|------|----------|----------|
| Python | 3.11+ | 见下方 |
| Node.js | 20+ | 见下方 |
| Redis | 7.0+ | `sudo apt install redis-server` |
| Conda | 最新版 | [Miniconda下载](https://docs.conda.io/en/latest/miniconda.html) |
| pnpm | 8+ | `npm install -g pnpm` |

---

## 2. 后端部署

### 2.1 检查 Python 环境
```bash
# 检查 Python 版本
python3 --version  # 应显示 3.11.x

# 如果没有 Python 3.11，使用 conda 安装
conda create -n student-manage python=3.11 -y
conda activate student-manage
```

### 2.2 安装后端依赖
```bash
cd /home/yufeng/student-manage-v3-security/student-manager/backend

# 安装依赖
pip install -r requirements.txt

# 关键依赖列表：
# - fastapi >= 0.110.0
# - uvicorn >= 0.27.0
# - python-multipart >= 0.0.9
# - pyrate-limiter >= 3.0.0
# - redis >= 5.0.0
# - python-jose >= 3.3.0
```

### 2.3 数据库初始化
```bash
# 数据库文件会自动创建在 data/student_manage.db
# 首次启动时会自动运行迁移
```

### 2.4 启动后端服务
```bash
# 开发模式（带热重载）
python main.py

# 或使用 uvicorn 直接启动
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**验证后端启动成功**:
```bash
curl http://localhost:8000/health
# 应返回: {"status":"healthy",...}
```

---

## 3. 前端部署

### 3.1 检查 Node.js 环境
```bash
# 检查 Node.js 版本
node --version  # 应显示 v20.x.x

# 检查 pnpm
pnpm --version  # 应显示 8.x.x
```

### 3.2 安装前端依赖
```bash
cd /home/yufeng/student-manage-v3-security/student-manager/frontend

# 安装依赖
pnpm install

# 如果 pnpm 未安装
npm install -g pnpm
```

### 3.3 配置开发环境
```bash
# 创建环境配置文件（如需要）
cp .env.example .env.local

# 编辑配置
VITE_API_BASE_URL=http://localhost:8000/api
```

### 3.4 启动前端服务
```bash
# 开发模式
pnpm dev

# 构建生产版本
pnpm build

# 预览生产构建
pnpm preview
```

**验证前端启动成功**:
```bash
curl http://localhost:3000
# 应返回 HTML 页面
```

---

## 4. Redis 部署

### 4.1 安装 Redis
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server -y

# macOS
brew install redis

# 启动 Redis
sudo systemctl start redis-server  # Linux
brew services start redis           # macOS
```

### 4.2 验证 Redis
```bash
redis-cli ping
# 应返回: PONG
```

### 4.3 Redis 配置（可选）
```bash
# 配置文件位置
sudo nano /etc/redis/redis.conf

# 关键配置项
bind 127.0.0.1
port 6379
requirepass your_password  # 生产环境建议设置密码
```

---

## 5. 完整环境一键启动

### 5.1 使用 Makefile（推荐）
```bash
# 在项目根目录
cd /home/yufeng/student-manage-v3-security/student-manager

# 启动所有服务（后台）
make dev

# 停止所有服务
make stop

# 查看日志
make logs
```

### 5.2 手动启动（前台）
```bash
# 终端 1: 启动 Redis（如未启动）
redis-server

# 终端 2: 启动后端
cd backend
conda activate student-manage
python main.py

# 终端 3: 启动前端
cd frontend
pnpm dev
```

---

## 6. 环境验证清单

部署完成后，请检查以下各项：

### 6.1 服务状态检查
- [ ] Redis 运行正常 `redis-cli ping`
- [ ] 后端服务运行正常 `curl http://localhost:8000/health`
- [ ] 前端服务运行正常 `curl http://localhost:3000`
- [ ] 数据库连接正常（后端日志无报错）
- [ ] 缓存连接正常（后端日志显示"Redis限流器已启用"）

### 6.2 功能验证
- [ ] 能访问首页 http://localhost:3000
- [ ] 能登录 admin/admin123
- [ ] 能查看学生列表
- [ ] 能进行签到操作
- [ ] API 文档可访问 http://localhost:8000/docs

---

## 7. 常见问题排查

### 7.1 端口冲突
```bash
# 检查端口占用
lsof -i :8000  # 后端端口
lsof -i :3000  # 前端端口
lsof -i :6379  # Redis 端口

# 释放端口
kill -9 <PID>
```

### 7.2 依赖安装失败
```bash
# 清理并重新安装前端依赖
cd frontend
rm -rf node_modules pnpm-lock.yaml
pnpm install

# 清理并重新安装后端依赖
cd backend
pip cache purge
pip install -r requirements.txt --force-reinstall
```

### 7.3 数据库权限问题
```bash
# 检查数据目录权限
ls -la data/

# 修复权限
chmod 755 data/
chmod 644 data/student_manage.db
```

### 7.4 Conda 环境激活失败
```bash
# 初始化 conda
conda init bash
source ~/.bashrc

# 手动激活环境
source /home/yufeng/miniconda3/bin/activate student-manage
```

---

## 8. 生产环境部署

### 8.1 使用 Docker（推荐）
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 8.2 手动部署
```bash
# 1. 构建前端
 cd frontend && pnpm build

# 2. 配置后端生产环境变量
export FASTAPI_ENV=production

# 3. 使用 systemd 管理服务
sudo systemctl enable student-manage-backend
sudo systemctl start student-manage-backend
```

---

## 9. 环境信息记录

部署完成后，记录以下信息：

```yaml
部署日期: 2025-03-21
部署人员: [你的名字]

后端服务:
  地址: http://localhost:8000
  健康检查: http://localhost:8000/health
  API文档: http://localhost:8000/docs

前端服务:
  地址: http://localhost:3000

Redis:
  地址: localhost:6379
  密码: [如设置了请记录]

数据库:
  位置: /home/yufeng/student-manage-v3-security/student-manager/data/student_manage.db
  备份: [备份策略]
```

---

**文档版本**: v1.0  
**最后更新**: 2025-03-21
