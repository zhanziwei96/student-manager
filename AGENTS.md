# ClassHub AI 助手速查手册

> **⚠️ 执行前强制阅读**: 
> 1. **先阅读** [ERRORS.md](./.agents/ERRORS.md) - 这是我必须遵守的禁令和强制流程
> 2. **然后检查**服务状态，避免重复部署

---

## 1. 通用禁令（绝对禁止）

| # | 禁令 | 违反后果 |
|---|------|----------|
| 1 | ❌ 不要在未检查服务状态的情况下重启服务 | 重复部署，端口冲突 |
| 2 | ❌ 不要快速连续执行停止+启动命令 | 残留进程导致启动失败 |
| 3 | ❌ 不要假设数据库/服务路径 | 操作错误的文件 |
| 4 | ❌ 不要在未验证的情况下认为操作成功 | 隐藏错误 |
| 6 | ❌ **禁止在碰到问题后回退组件版本** | 掩盖问题，重复犯错 |
| 7 | ❌ **禁止在非虚拟环境的 python 环境下运行 python 命令** | 模块找不到，环境混乱 |
| 8 | ❌ **禁止修改后端代码后不检查/更新对应测试** | 测试失效，覆盖率下降，隐藏回归错误 |
| 9 | ❌ **禁止在未阅读完所有相关代码的情况下直接修复整改** | 破坏项目结构一致性，重复造轮子，引入不一致的实现 |

---

## 2. 执行前强制检查清单

```bash
# 1. 环境检查 (必须)
which python  # 确认是 miniconda 路径

# 2. 服务状态检查 (必须)
curl -s http://localhost:8000/api/health  # 后端是否已运行？
curl -s http://localhost:5173 > /dev/null && echo "前端运行中"  # 前端是否已运行？

# 3. 数据库路径确认 (涉及 DB 操作时必须)
python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"
```

**决策逻辑**: 服务已运行 → 不需要重启；服务未运行 → 按重启流程执行

---

## 3. 服务重启强制流程

**禁止**直接执行 `python main.py` 或 `pnpm dev`。

```bash
# 后端重启
pkill -f "python main.py" 2>/dev/null || true
sleep 3  # 必须等待！
ps aux | grep "python.*main.py" | grep -v grep  # 检查残留
cd /home/yufeng/student-manager/backend
conda run -n student-manage ENV=production python main.py &
sleep 5
curl -s http://localhost:8000/api/health  # 必须验证！

# 前端重启
pkill -f "pnpm dev" 2>/dev/null || true
sleep 2
cd /home/yufeng/student-manager/frontend-v3
pnpm dev &
sleep 3
curl -s http://localhost:5173 > /dev/null && echo "前端运行中"  # 必须验证！
```

---

## 4. 常用命令速查

### 启动服务

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

# 并发保护测试（BE-008）
pytest tests/unit/crud/test_concurrent_*.py -v
```

**修改后端代码后必须询问用户**: 
> "修改/新增功能已完成，是否需要运行测试？
> - 运行全部测试: `pytest tests/ -v`
> - 仅单元测试: `pytest tests/unit -v`
> - 仅集成测试: `pytest tests/integration -v`
> - 不需要测试"

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

## 5. 关键路径

| 项目 | 路径 |
|------|------|
| 后端代码 | `/home/yufeng/student-manager/backend/` |
| 前端代码 | `/home/yufeng/student-manager/frontend-v3/` |
| 旧版前端 | `/home/yufeng/student-manager/frontend/` (不再维护) |
| 数据库 | `/home/yufeng/student-manager/backend/data/class_system.db` |
| 测试代码 | `/home/yufeng/student-manager/tests/` |
| 迁移脚本 | `/home/yufeng/student-manager/migrations/` |

---

## 6. 技术架构

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
- API 响应访问: 必须用 `res.data.xxx`，禁止 `res.xxx`

### 数据库
- SQLite 文件数据库
- 数据库路径: `backend/data/class_system.db`
- 配置项: `DATABASE__PATH`（注意双下划线）

---

## 7. 测试结构

```
tests/
├── unit/                    # 单元测试 (121个)
│   ├── test_jwt.py         # JWT 工具测试 (11个)
│   ├── test_jwt_deps.py    # JWT 依赖测试 (8个)
│   ├── crud/               # CRUD 测试
│   │   ├── test_concurrent_score_update.py    # 并发分数更新保护 (4个) - BE-008
│   │   └── test_concurrent_login_failure.py   # 并发登录失败保护 (7个) - BE-008
│   └── ...                 # 其他测试
└── integration/            # 集成测试 (97个)
    ├── test_jwt_auth.py    # JWT 认证集成测试 (13个)
    └── ...                 # 其他测试
```

---

## 8. 环境要求

| 依赖 | 版本 | 检查命令 |
|------|------|----------|
| Python | 3.11+ | `python --version` |
| Conda | 最新 | `conda --version` |
| Node.js | 20+ | `node --version` |
| pnpm | 8+ | `pnpm --version` |

**必须激活虚拟环境**: `conda activate student-manage`

---

## 9. 文档导航

| 文档 | 内容 |
|------|------|
| [.agents/ERRORS.md](./.agents/ERRORS.md) | 常见错误记录、执行约束清单、纠错记录 |
| [.agents/DEPLOYMENT.md](./.agents/DEPLOYMENT.md) | 完整部署指南 |
| [.agents/CONFIG_GUIDE.md](./.agents/CONFIG_GUIDE.md) | 配置管理说明 |
| [migrations/README.md](./migrations/README.md) | 数据库迁移（已完成） |
| [tests/README.md](./tests/README.md) | 测试说明 |

---

## 10. 纠错机制

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

### 如何处理纠错反馈

1. **确认收到**: "已收到纠错反馈，将更新约束清单"
2. **分析错误**: 确定是流程缺失、知识错误还是禁令违反
3. **更新 ERRORS.md**:
   - 如果是新类型的错误 → 添加到对应约束章节
   - 如果需要禁止 → 加入通用禁令表
   - 更新纠错记录表
4. **确认更新**: "已更新 ERRORS.md，新增约束: [简述]"

### 当前已纠正的错误模式

见 [.agents/ERRORS.md 纠错记录](./.agents/ERRORS.md#纠错记录)

---

**最后更新**: 2026-03-26 (新增禁令：修改前必须阅读相关代码)
**架构版本**: FastAPI + SQLModel
