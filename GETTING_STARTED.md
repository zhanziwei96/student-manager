# ClassHub 开发者快速开始指南

---

**文档版本**: v1.0  
**最后更新**: 2026-04-05  
**适用版本**: v3.0.0+  
**预计阅读时间**: 15分钟  
**状态**: ✅ 已同步代码

---

## 概述

本指南帮助新开发者快速搭建 ClassHub 开发环境，从克隆代码到运行第一个功能。

## 环境要求

| 软件 | 版本要求 | 检查命令 |
|------|----------|----------|
| Python | 3.11+ | `python --version` |
| Conda | 最新 | `conda --version` |
| Node.js | 20+ | `node --version` |
| pnpm | 8+ | `pnpm --version` |
| SQLite | 3.35+ | `sqlite3 --version` |
| Git | 任意 | `git --version` |

## 5分钟快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd student-manager
```

### 2. 启动后端

```bash
# 创建并激活 Conda 环境
conda create -n student-manage python=3.11 -y
conda activate student-manage

# 安装依赖
cd backend
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动服务
ENV=development python main.py
```

后端将在 http://localhost:8000 运行

### 3. 启动前端

```bash
# 新开终端，进入前端目录
cd frontend-v3

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

前端将在 http://localhost:5173 运行

### 4. 验证安装

```bash
# 检查后端健康状态
curl http://localhost:8000/api/v1/health

# 访问前端页面
open http://localhost:5173
```

### 5. 登录测试

使用默认管理员账号登录：
- **用户名**: `admin`
- **密码**: `admin123`

---

## 详细环境搭建

### 后端环境详细配置

#### 1. Conda 环境配置

```bash
# 创建环境
conda create -n student-manage python=3.11 -y

# 激活环境
conda activate student-manage

# 验证环境
which python
# 期望输出: /home/yourname/miniconda3/envs/student-manage/bin/python

# 安装依赖
cd backend
pip install -r requirements.txt
```

#### 2. 环境变量配置

创建 `.env` 文件：

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# 应用配置
ENV=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 数据库配置（双下划线分隔嵌套属性）
DATABASE__PATH=./data/class_system.db
DATABASE__TIMEOUT=30

# 安全配置（生产环境必须修改）
SECURITY__SECRET_KEY=your-secret-key-change-in-production
SECURITY__MAX_LOGIN_FAILURES=10
SECURITY__LOCKOUT_DURATION_MINUTES=30

# JWT配置
JWT__ACCESS_TOKEN_EXPIRE_MINUTES=1440
JWT__ALGORITHM=HS256
JWT__COOKIE_NAME=access_token

# CORS配置（开发环境）
SECURITY__CORS_ORIGINS=["http://localhost:5173"]

# 限流配置
RATE_LIMIT__ENABLED=true
RATE_LIMIT__LOGIN_MAX_REQUESTS=5
RATE_LIMIT__CHECKIN_MAX_REQUESTS=10
```

#### 3. 数据库初始化

```bash
# 数据库会在首次启动时自动创建
# 如需手动初始化，执行迁移脚本
sqlite3 backend/data/class_system.db < migrations/migrate_v1_to_v2.sql
```

#### 4. 启动后端服务

```bash
# 开发模式（热重载）
ENV=development uvicorn main:app --reload --port 8000

# 或使用 Python 直接启动
ENV=development python main.py
```

### 前端环境详细配置

#### 1. Node.js 环境检查

```bash
# 检查版本
node --version  # v20.x.x
pnpm --version  # 8.x.x

# 如未安装 pnpm
npm install -g pnpm
```

#### 2. 安装依赖

```bash
cd frontend-v3

# 安装项目依赖
pnpm install

# 验证安装
pnpm list vue
```

#### 3. 配置开发环境

前端配置位于 `frontend-v3/.env`：

```bash
# 创建环境文件
cat > .env << EOF
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=ClassHub
EOF
```

#### 4. 启动前端服务

```bash
# 开发模式
pnpm dev

# 或使用 Vite 直接启动
npx vite
```

---

## 项目结构速览

```
student-manager/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── core/              # 核心配置
│   │   ├── crud/              # 数据库操作
│   │   └── models/            # 数据模型
│   ├── data/                  # SQLite 数据库
│   ├── main.py                # 应用入口
│   └── requirements.txt       # Python依赖
│
├── frontend-v3/               # Vue3 + TypeScript 前端
│   ├── src/
│   │   ├── api/               # API 请求
│   │   ├── components/        # UI组件
│   │   ├── composables/       # 组合式函数
│   │   ├── features/          # 功能模块
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # Pinia状态
│   │   └── views/             # 页面组件
│   ├── test/                  # 测试文件
│   └── package.json
│
├── tests/                     # 后端测试
│   ├── unit/                  # 单元测试
│   └── integration/           # 集成测试
│
├── migrations/                # 数据库迁移脚本
├── docs/                      # 项目文档
└── .agents/                   # 开发规范
```

---

## 开发工作流

### 日常开发流程

```bash
# 1. 检查服务状态
make status

# 2. 如未启动，启动服务
# 终端1 - 后端
cd backend && conda run -n student-manage ENV=development python main.py

# 终端2 - 前端
cd frontend-v3 && pnpm dev

# 3. 开发代码...

# 4. 运行测试
pytest tests/ -v              # 后端测试
cd frontend-v3 && pnpm test:run  # 前端测试
```

### 代码修改检查清单

#### 后端修改

- [ ] 修改代码后查找相关测试文件
- [ ] 运行相关测试验证修改
- [ ] 确保测试通过

```bash
# 查找相关测试
find tests -name "*<模块名>*" -type f

# 运行相关测试
pytest tests/unit/test_<模块>.py -v
pytest tests/integration/test_<模块>_api*.py -v
```

#### 前端修改

- [ ] 评估是否需要创建/修改测试
- [ ] 运行前端测试
- [ ] 检查类型错误

```bash
cd frontend-v3

# 类型检查
pnpm type-check

# 运行测试
pnpm test:run

# 代码检查
pnpm lint
```

---

## 常用命令速查

### 后端命令

```bash
# 启动服务
ENV=development python main.py

# 运行测试
pytest tests/ -v                    # 全部测试
pytest tests/unit -v                # 仅单元测试
pytest tests/integration -v         # 仅集成测试

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 数据库操作
sqlite3 backend/data/class_system.db ".tables"
sqlite3 backend/data/class_system.db ".schema users"
```

### 前端命令

```bash
# 开发
pnpm dev                            # 启动开发服务器
pnpm build                          # 生产构建
pnpm preview                        # 预览生产构建

# 测试
pnpm test                           # 交互式测试
pnpm test:run                       # 运行所有测试
npx vitest run --coverage           # 生成覆盖率报告

# 代码质量
pnpm lint                           # 代码检查
pnpm type-check                     # 类型检查
```

### Makefile 快捷命令

```bash
# 在项目根目录
make status                         # 检查服务状态
make dev-backend                    # 启动后端
make dev-frontend                   # 启动前端
make stop                           # 停止所有服务
make logs                           # 查看日志
```

---

## 故障排查

### 常见问题

#### 1. Python 模块找不到

```bash
# 错误: ModuleNotFoundError: No module named 'app'

# 解决: 确保激活 Conda 环境
conda activate student-manage
which python  # 确认是 miniconda 路径
```

#### 2. 端口冲突

```bash
# 错误: Address already in use

# 解决: 查找并停止占用进程
lsof -i :8000
kill -9 <PID>

# 或使用 Makefile
make stop
```

#### 3. 前端依赖安装失败

```bash
# 清理后重新安装
cd frontend-v3
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

#### 4. 数据库连接错误

```bash
# 检查数据库路径
python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"

# 检查数据库文件是否存在
ls -la backend/data/class_system.db
```

### 调试技巧

#### 后端调试

```bash
# 查看后端日志
tail -f backend/logs/app.log

# 启用详细日志
ENV=development LOG_LEVEL=debug python main.py

# 使用 pdb 调试
python -m pdb main.py
```

#### 前端调试

```bash
# 浏览器开发者工具
# F12 打开 Network 标签查看 API 请求

# Vue DevTools 浏览器扩展
# 安装 Vue.js devtools 扩展
```

---

## 下一步

### 学习资源

1. **[backend/README.md](./backend/README.md)** - 深入了解后端架构
2. **[frontend-v3/docs/ARCHITECTURE.md](./frontend-v3/docs/ARCHITECTURE.md)** - 前端架构指南
3. **[docs/API_EXAMPLES.md](./docs/API_EXAMPLES.md)** - API 使用示例
4. **[CLAUDE.md](./CLAUDE.md)** - 开发规范和约束

### 参与贡献

1. 阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)
2. 查看 [docs/REQUIREMENTS.md](./docs/REQUIREMENTS.md) 了解功能规划
3. 从 [docs/FAQ.md](./docs/FAQ.md) 了解常见问题

### 获取帮助

- 查看 [docs/FAQ.md](./docs/FAQ.md) 常见问题解答
- 检查 [.agents/ERRORS.md](./.agents/ERRORS.md) 约束清单
- 查看后端日志 `backend/logs/app.log`

---

## 验证清单

完成本指南后，你应该能够：

- [ ] 成功启动后端服务（http://localhost:8000）
- [ ] 成功启动前端服务（http://localhost:5173）
- [ ] 使用默认账号登录系统
- [ ] 运行后端测试并通过
- [ ] 运行前端测试并通过
- [ ] 理解项目基本结构

---

**恭喜！** 你已完成 ClassHub 开发环境的搭建。

如有问题，请参考 [docs/FAQ.md](./docs/FAQ.md) 或查看项目文档。

---

**文档版本**: v1.0  
**最后更新**: 2026-04-05
