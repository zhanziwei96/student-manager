# ClassHub AI 助手速查手册

> **⚠️ 执行前强制阅读**: 
> 1. **先阅读** [ERRORS.md 执行约束清单](./ERRORS.md) - 这是我必须遵守的禁令和强制流程
> 2. **然后检查**服务状态，避免重复部署

---

## 1. 快速检查清单

```bash
# 检查服务状态（优先执行）
curl http://localhost:8000/api/health  # 后端
curl http://localhost:5173             # 前端 (frontend-v3)

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
cd frontend-v3 && pnpm install
```

#### 日常启动

**方式1: 使用 Makefile**

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

**方式2: 手动启动**

```bash
# 终端1: 后端（生产环境）
cd backend && conda activate student-manage && ENV=production python main.py

# 终端2: 前端 (frontend-v3)
cd frontend-v3 && pnpm dev
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
| 前端代码 | `/home/yufeng/student-manager/frontend-v3/` |
| 旧版前端 | `/home/yufeng/student-manager/frontend/` (不再维护) |
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

### 前端（Vue3 + Tailwind CSS v4）
- **使用 Tailwind CSS v4**，不是 Naive UI/Element Plus
- 深色主题: 背景 `#030307`，主色 `#6366f1`
- 技术栈: Vue 3.5 + TypeScript + TanStack Query + Pinia

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

---

## 9. 纠错机制

### 纠错反馈模板（复制使用）

当你发现我犯了错误，请**复制以下模板**填写并发送：

```markdown
## 纠错反馈

**错误类型**: [环境/前端/后端/测试/通用]

**错误描述**: 
[描述我具体做了什么错误操作]

**正确做法**: 
[描述应该怎么做]

**是否需要加入禁令**: [是/否]
- 如果是"是"，建议禁令表述: [如"禁止在未检查服务状态的情况下重启"]

**相关代码/命令**: 
```
[如果有具体代码或命令，贴在这里]
```
```

### 示例

```markdown
## 纠错反馈

**错误类型**: 通用

**错误描述**: 
在没有检查服务状态的情况下执行了重启命令，导致端口冲突。

**正确做法**: 
执行重启前必须用 curl 检查 health 端点，确认服务未运行后再重启。

**是否需要加入禁令**: 是
- 建议禁令表述: 禁止在未检查服务状态的情况下重启服务

**相关代码/命令**: 
```bash
# 错误 - 直接重启
pkill -f "python main.py"
python main.py

# 正确 - 先检查
curl -s http://localhost:8000/api/health || echo "服务未运行"
# 确认未运行后再重启
```
```

### 如何处理我的纠错反馈

作为 AI，当我收到上述格式的纠错反馈后，我会：

1. **确认收到**: "已收到纠错反馈，将更新约束清单"
2. **分析错误**: 确定是流程缺失、知识错误还是禁令违反
3. **更新 ERRORS.md**:
   - 如果是新类型的错误 → 添加到对应约束章节
   - 如果需要禁止 → 加入通用禁令表
   - 更新纠错记录表
4. **确认更新**: "已更新 ERRORS.md，新增约束: [简述]"

### 当前已纠正的错误模式

见 [ERRORS.md 纠错记录](./ERRORS.md#纠错记录)

---

---

## 10. 启动 Prompt

每次开启新 Session 时，复制以下 Prompt 发送给 AI：

```markdown
请首先阅读 `/home/yufeng/student-manager/.agents/ERRORS.md` 中的**执行约束清单**，并确认你已理解：

1. **通用禁令** - 绝对禁止的行为
2. **执行前强制检查清单** - 执行命令前必须完成的检查
3. **相关约束** - 与本次任务相关的具体约束（如前端/后端/数据库等）

阅读完成后回复："已阅读约束清单，现在开始执行任务。"

然后按照检查清单顺序执行操作，不要跳过任何验证步骤。
```

---

**最后更新**: 2026-03-23 (约束清单机制更新)
**架构版本**: FastAPI + SQLModel
