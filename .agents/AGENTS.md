# ClassHub AI 助手速查手册

> **使用前必读**: 处理任何请求前，先检查服务状态，避免重复部署。

---

## 1. 快速检查清单

```bash
# 检查服务状态（优先执行）
curl http://localhost:8000/health  # 后端
curl http://localhost:3000         # 前端
redis-cli ping                     # Redis

# 如果都正常返回，环境已就绪 ✅
```

---

## 2. 常用命令速查

### 启动服务

#### 首次部署（环境准备）

```bash
cd /home/yufeng/student-manager

# 1. 后端环境
conda create -n student-manage python=3.11 -y
conda activate student-manage
cd backend && pip install -r requirements.txt

# 2. 前端依赖
cd frontend && pnpm install

# 3. Redis (Ubuntu)
sudo apt install redis-server
sudo systemctl start redis-server
redis-cli ping  # 验证: 应返回 PONG
```

#### 日常启动

**方式1: 使用 Makefile**

```bash
cd /home/yufeng/student-manager

# 检查状态
make status

# 启动服务（开两个终端）
make dev-backend   # 终端1: 启动后端
make dev-frontend  # 终端2: 启动前端

# 停止服务
make stop

# 查看日志
make logs
```

**方式2: 手动启动**

```bash
# 终端1: 后端
cd backend && conda activate student-manage && python main.py

# 终端2: 前端
cd frontend && pnpm dev
```

### 运行测试
```bash
# 全部测试
pytest tests/ -v

# 仅冒烟测试（快速验证）
pytest tests/integration/test_smoke.py -v

# 仅单元测试
pytest tests/unit -v
```

### 数据库操作
```bash
# 检查数据库路径
python -c "from infrastructure.config import get_settings; import os; print(os.path.abspath(get_settings().database.path))"

# 连接数据库
sqlite3 /home/yufeng/student-manager/backend/data/student_manage.db

# 查看表结构
.schema users
.schema students
```

---

## 3. 关键路径

| 项目 | 路径 |
|------|------|
| 后端代码 | `/home/yufeng/student-manager/backend/` |
| 前端代码 | `/home/yufeng/student-manager/frontend/` |
| 数据库 | `/home/yufeng/student-manager/backend/data/` |
| 测试代码 | `/home/yufeng/student-manager/tests/` |
| 迁移脚本 | `/home/yufeng/student-manager/migrations/` |

---

## 4. 技术约束

### 前端（Vue3 + Naive UI）
- **必须使用 Naive UI**，不是 Element Plus
- 深色主题: 背景 `#0a0a0f`，主色 `#6366f1`

### 后端（FastAPI + DDD）
- 分层架构: Interface → Application → Domain ← Infrastructure
- Domain 层不能依赖 Infrastructure 层

### 数据库
- SQLite 文件数据库
- 配置项: `DATABASE__PATH`（注意双下划线）

---

## 5. 测试结构

```
tests/
├── unit/                    # 单元测试（188个）
│   ├── domain/             # 100个 - 实体、值对象
│   ├── application/        # 33个 - 应用服务
│   └── infrastructure/     # 55个 - Repository
└── integration/            # 集成测试（24个）
    ├── test_smoke.py       # 冒烟测试
    ├── test_auth_api.py    # 认证
    ├── test_student_api.py # 学生管理
    └── test_user_api.py    # 用户管理
```

---

## 6. 环境要求

| 依赖 | 版本 | 检查命令 |
|------|------|----------|
| Python | 3.11+ | `python --version` |
| Conda | 最新 | `conda --version` |
| Node.js | 20+ | `node --version` |
| pnpm | 8+ | `pnpm --version` |
| Redis | 7.0+ | `redis-cli ping` |

**必须激活虚拟环境**:
```bash
conda activate student-manage
```

---

## 7. 工作流程规范

### 修改和新增功能后

**修改或新增功能完成后，必须询问用户是否需要运行测试。**

```
修改/新增功能已完成，是否需要运行测试？
- 运行全部测试: pytest tests/ -v
- 仅冒烟测试: pytest tests/integration/test_smoke.py -v
- 不需要测试
```

---

## 8. 文档导航

| 文档 | 内容 |
|------|------|
| [ERRORS.md](./ERRORS.md) | 常见错误记录 |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | 完整部署指南 |
| [CONFIG_GUIDE.md](./CONFIG_GUIDE.md) | 配置管理说明 |
| [migrations/README.md](../migrations/README.md) | 数据库迁移 |
| [tests/README.md](../tests/README.md) | 测试说明 |

---

**最后更新**: 2026-03-21
