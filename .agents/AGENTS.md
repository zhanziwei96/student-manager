# ClassHub AI 助手速查手册

> **使用前必读**: 处理任何请求前，先检查服务状态，避免重复部署。

---

## 1. 快速检查清单

```bash
# 检查服务状态（优先执行）
curl http://localhost:8000/api/health  # 后端
curl http://localhost:3000             # 前端

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
# 终端1: 后端（生产环境）
cd backend && conda activate student-manage && ENV=production python main.py

# 终端2: 前端
cd frontend && pnpm dev
```

### 运行测试
```bash
# 全部测试
pytest tests/ -v

# 仅单元测试
pytest tests/unit -v

# 仅集成测试
pytest tests/integration -v
```

### 数据库操作
```bash
# 检查数据库路径
python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"

# 连接数据库
sqlite3 /home/yufeng/student-manager/backend/data/class_system.db

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
| 数据库 | `/home/yufeng/student-manager/backend/data/class_system.db` |
| 测试代码 | `/home/yufeng/student-manager/tests/` |
| 迁移脚本 | `/home/yufeng/student-manager/migrations/` |

---

## 4. 技术架构

### 当前架构（FastAPI + SQLModel）

```
backend/
├── app/
│   ├── api/           # API路由
│   │   ├── deps.py    # 依赖注入
│   │   └── routes/    # 路由处理器
│   ├── core/          # 核心组件
│   │   ├── config.py  # 配置管理
│   │   ├── db.py      # 数据库连接
│   │   └── security.py # 安全工具
│   ├── crud/          # 数据库操作
│   └── models/        # 数据模型
└── main.py            # 应用入口
```

**架构特点：**
- 使用 FastAPI 框架
- SQLModel 作为 ORM（SQLAlchemy + Pydantic）
- 分层结构：API → CRUD → Models
- JWT + HttpOnly Cookie 认证

### 前端（Vue3 + Naive UI）
- **使用 Naive UI**，不是 Element Plus
- 深色主题: 背景 `#0a0a0f`，主色 `#6366f1`

### 数据库
- SQLite 文件数据库
- 数据库路径: `backend/data/class_system.db`
- 配置项: `DATABASE__PATH`（注意双下划线）

---

## 5. 测试结构

```
tests/
├── unit/                    # 单元测试
│   ├── test_jwt.py         # JWT 工具测试 (11个)
│   ├── test_jwt_deps.py    # JWT 依赖测试 (8个)
│   └── ...                 # 其他测试
└── integration/            # 集成测试
    ├── test_jwt_auth.py    # JWT 认证集成测试 (13个)
    └── ...                 # 其他测试
```

---

## 6. 环境要求

| 依赖 | 版本 | 检查命令 |
|------|------|----------|
| Python | 3.11+ | `python --version` |
| Conda | 最新 | `conda --version` |
| Node.js | 20+ | `node --version` |
| pnpm | 8+ | `pnpm --version` |

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
- 仅单元测试: pytest tests/unit -v
- 仅集成测试: pytest tests/integration -v
- 不需要测试
```

---

## 8. 文档导航

| 文档 | 内容 |
|------|------|
| [ERRORS.md](./ERRORS.md) | 常见错误记录 |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | 完整部署指南 |
| [CONFIG_GUIDE.md](./CONFIG_GUIDE.md) | 配置管理说明 |
| [migrations/README.md](../migrations/README.md) | 数据库迁移（已完成） |
| [tests/README.md](../tests/README.md) | 测试说明 |

---

**最后更新**: 2026-03-22 (JWT认证更新)
**架构版本**: FastAPI + SQLModel
