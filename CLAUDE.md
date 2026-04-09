# CLAUDE.md

## ⚠️ 执行前强制检查清单

**每次执行操作前，我必须显式勾选以下清单。如果缺少勾选，请打断我要求重新确认。**

### 后端操作
- [ ] **Python 环境**: 使用 `conda run -n student-manage` 或已激活环境 (`conda activate student-manage`)
  - 验证: `which python` 输出包含 `miniconda`
- [ ] **修改代码后**: 已查找并检查相关测试文件（单元测试+集成测试）
  - 单元测试: `tests/unit/test_<模块>.py` 或 `tests/unit/<模块>/test_*.py`
  - 集成测试: `tests/integration/test_<模块>_api*.py`
- [ ] **重启服务前**: 已运行 `make status` 或 `curl -s --max-time 5 http://localhost:8000/api/v1/health` 检查状态
- [ ] **服务重启**: 按完整流程（停止→等待3秒→检查残留→启动→等待5秒→验证）
  - 禁止快速连续执行停止+启动命令
- [ ] **数据库操作**: 已确认实际路径
  - `python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"`

### Read 工具强制预检（每次调用前必须执行）
- [ ] **参数检查**: 在 commentary 中显式输出一行确认（如：`Read preflight: limit=200, offset=1. OK.`）
  - `limit` 必须是正整数（> 0），禁止传负数
  - `offset` >= 1
  - 超大文件优先用 `Grep`，不盲目读全文
  - **未输出此行即调用 Read，视为违规**

### 前端操作
- [ ] **修改代码后**: 已评估是否需要创建/修改测试
- [ ] **重启服务前**: 已检查当前状态
- [ ] **API 响应**: 使用 `res.data.xxx` 而非 `res.xxx`
- [ ] **Tailwind v4**: 自定义 `@theme` 时保留 `--spacing: 0.25rem` 或使用 `@theme inline`

### 通用操作
- [ ] **curl 命令**: 已添加 `--max-time 10` 或 `--connect-timeout 5` 超时
- [ ] **未经同意**: 不擅自修改功能或简化需求
- [ ] **禁止回退**: 碰到问题不回退组件版本，先尝试修复或报告

**完整约束详见**: `.agents/CHECKLIST.md` 和 `.agents/ERRORS.md`

---

本文档为 Claude Code (claude.ai/code) 提供本仓库的代码编写指南。
## 语言规范
- 所有对话和文档都使用中文
- 文档使用 markdown 格式
## 项目概述

ClassHub（班级管理系统）是一个前后端分离的班级管理系统，采用 Python FastAPI 后端和 Vue 3 TypeScript 前端。功能包括学生管理、网页签到、分数统计和数据可视化。

## 常用命令

### 开发命令

```bash
# 重启服务前检查状态
make status

# 启动后端（终端1）- 需要 conda 环境
cd backend && conda run -n student-manage ENV=production python main.py

# 启动前端（终端2）- 使用 frontend-v3，不是旧版 frontend
cd frontend-v3 && pnpm dev

# 或使用 Makefile 快捷命令
make dev-backend    # 终端1
make dev-frontend   # 终端2
make stop           # 停止所有服务
make logs           # 查看最新日志
make status         # 检查服务健康状态
```

### 测试命令

```bash
# 后端测试（在项目根目录运行）
pytest tests/ -v                    # 全部测试（467个）
pytest tests/unit -v                # 仅单元测试
pytest tests/integration -v         # 仅集成测试
pytest tests/unit/test_jwt.py -v    # 单个测试文件

# 前端测试（在 frontend-v3/ 目录运行）
cd frontend-v3
pnpm test:run                       # 运行所有测试（130个）
pnpm test                           # 交互式测试模式
```

### 环境要求

- **Python**: 3.11+，使用 Conda 环境 `student-manage`
- **Node.js**: 20+，使用 pnpm 8+
- **数据库**: SQLite，位于 `backend/app/data/class_system.db`

运行 Python 命令前必须激活 Conda 环境：
```bash
conda activate student-manage
# 或使用: conda run -n student-manage python <脚本>
```

## 架构说明

### 后端（FastAPI + SQLModel）

位于 `backend/` 目录，采用分层架构：

```
backend/app/
├── api/           # API 层（路由、依赖注入）
│   ├── deps.py    # 依赖注入（get_current_user 等）
│   └── routes/    # 路由处理器
├── core/          # 核心工具
│   ├── config.py  # 配置管理（pydantic-settings）
│   ├── db.py      # 数据库连接
│   └── security.py # JWT、密码哈希（bcrypt）
├── crud/          # 数据库操作层
├── models/        # SQLModel 实体 + Pydantic 模式
└── events/        # 事件处理器
```

**关键模式：**
- 所有 API 响应使用 `app.models.constants` 中的常量（ApiResponseConst、MessageConst）
- JWT Token 包含：`sub` (用户ID)、`username`、`name`、`role`、`is_admin`
- 访问响应数据使用 `res.data.xxx`，禁止使用 `res.xxx`
- 时区：JWT 过期时间必须使用 `Asia/Shanghai` 时区
- 密码哈希使用 `bcrypt`（自动处理盐值），通过 `verify_password()` / `hash_password()` 使用

### 前端（Vue 3.5 + TypeScript）

位于 `frontend-v3/` 目录，采用特性化组织方式：

```
frontend-v3/src/
├── api/           # API 客户端函数
├── assets/        # 静态资源
├── components/    # UI 组件（ui/ + admin/ + teacher/）
├── composables/   # Vue 组合式函数（useToast 是全局的）
├── features/      # 特性化模块
├── layouts/       # 布局组件
├── lib/           # 工具函数
├── router/        # Vue Router 配置
├── stores/        # Pinia 状态管理
├── styles/        # 样式文件
├── types/         # TypeScript 类型定义
└── views/         # 页面级组件
```

**关键模式：**
- Tailwind CSS v4 自定义主题：背景色 `#030307`，主色 `#6366f1`
- 自定义 `@theme` 时必须保留 `--spacing: 0.25rem` 或使用 `@theme inline`
- API 响应：后端返回 `{success, data, message}` 格式，通过 `res.data.xxx` 访问
- 使用 `@tanstack/vue-query` 进行服务端状态管理和缓存
- HTTP 请求使用 `ofetch`
- 图标来自 `lucide-vue-next`

### 数据库

- SQLite 文件数据库，位于 `backend/app/data/class_system.db`
- 配置使用双下划线格式：`DATABASE__PATH`、`SECURITY__SECRET_KEY`（不是单下划线）
- 查看实际路径：`python -c "from backend.app.core.config import get_settings; print(get_settings().get_database_path())"`
- 集成测试使用内存数据库（隔离）

### 测试结构

```
tests/
├── unit/              # 单元测试（测试单个函数）
│   ├── crud/         # CRUD 层测试
│   └── test_*.py     # 模块测试
├── integration/       # API 集成测试
└── smoke/            # 端到端冒烟测试
```

## 关键约束

### 绝对禁止（ Universal Prohibitions）

| # | 禁令 | 违反后果 |
|---|------|----------|
| 1 | ❌ 不要在未检查服务状态的情况下重启服务 | 重复部署，端口冲突 |
| 2 | ❌ 不要快速连续执行停止+启动命令 | 残留进程导致启动失败 |
| 3 | ❌ 不要假设数据库/服务路径 | 操作错误的文件 |
| 4 | ❌ 不要在未验证的情况下认为操作成功 | 隐藏错误 |
| 5 | ❌ **禁止在碰到问题后回退组件版本** | 掩盖问题，重复犯错 |
| 6 | ❌ **禁止在非虚拟环境的 python 环境下运行 python 命令** | 模块找不到，环境混乱 |
| 7 | ❌ **禁止修改后端代码后不检查/更新对应测试** | 测试失效，覆盖率下降 |
| 8 | ❌ **禁止修改 Vue/TS 文件后不创建或修改测试** | 前端类型变更无测试覆盖 |
| 9 | ❌ **禁止未经用户明确同意擅自修改功能或简化需求** | 违背用户意图，破坏信任 |
| 10 | ❌ **禁止在未阅读完所有相关代码的情况下直接修复整改** | 破坏项目结构一致性 |

### 后端开发约束

#### 密码验证（SEC-003 修复后）
**必须使用新接口**：
```python
from app.core.security import verify_password, hash_password

# ✅ 正确 - bcrypt 自动处理盐值
is_valid = verify_password("plain_password", stored_hash)
new_hash = hash_password("new_password")

# ❌ 错误 - 旧接口已弃用
# is_valid = verify_password_hash("plain_password", stored_hash, salt)
```

#### JWT 时区处理
**所有 JWT Token 的过期时间必须使用 Asia/Shanghai 时区**：
```python
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ✅ 正确
now = datetime.now(ZoneInfo("Asia/Shanghai"))
expire = now + timedelta(hours=24)

# ❌ 错误 - 可能导致时区不一致
# expire = datetime.utcnow() + timedelta(hours=24)
```

#### API 响应常量
**禁止硬编码响应字段名**，必须使用常量：
```python
from app.models.constants import ApiResponseConst, MessageConst

# ✅ 正确
return {
    ApiResponseConst.SUCCESS: True,
    ApiResponseConst.MESSAGE: MessageConst.USER_CREATED,
    ApiResponseConst.DATA: user.model_dump()
}

# ❌ 错误
# return {"success": True, "message": "用户创建成功"}
```

#### JWT Claims 访问
**禁止假设字段存在**，始终使用 `.get()` 方法：
```python
# ✅ 正确
user_id = user.get("sub")

# ❌ 错误 - 可能报错
# user_id = user["sub"]
```

#### 限流状态码
限流触发时必须返回 **429 Too Many Requests**，而非 503：
```python
# ✅ 正确
raise HTTPException(status_code=429, detail="请求过于频繁")

# ❌ 错误
# raise HTTPException(status_code=503, detail="服务不可用")
```

#### 环境变量格式
使用**双下划线**访问嵌套配置：
```bash
# ✅ 正确
DATABASE__PATH=./data/class_system.db
SECURITY__SECRET_KEY=your-secret

# ❌ 错误 - 单下划线会被忽略
# DATABASE_PATH=xxx
```

### 前端开发约束

#### API 响应处理
后端返回格式: `{success: true, data: {...}, message: "..."}`
**禁止直接访问 `res.xxx`**，必须访问 `res.data`：
```typescript
// ❌ 错误
res.user.role

// ✅ 正确
res.data.role
```

#### Tailwind CSS v4
自定义 `@theme` 会**完全覆盖**默认主题，必须保留 `--spacing`：
```css
/* ✅ 正确 */
@theme inline {
  --color-primary: #6366f1;
}

/* 或 */
@theme {
  --spacing: 0.25rem;  /* 必须保留！ */
  --color-primary: #6366f1;
}
```

### 测试执行约束

#### 运行路径
```bash
# ✅ 正确 - 在项目根目录运行
pytest tests/ -v

# ❌ 错误 - 不要 cd 到 tests 目录
```

#### 修改后流程
修改或新增功能后，**必须**询问用户是否需要运行测试。

**详细约束清单和执行流程参见**：
- `.agents/ERRORS.md` - 完整约束清单和纠错记录
- `.agents/CHECKLIST.md` - 执行前详细检查清单

## 配置说明

环境变量配置在 `backend/.env` 文件中：
- `ENV=production|development|testing`
- `DATABASE__PATH`（必须使用双下划线）
- `SECURITY__SECRET_KEY`（必须使用双下划线）
- 更多选项参见 `backend/.env.example`

## 文档索引

### 入门指南
| 文档 | 说明 |
|------|------|
| `README.md` | 项目主文档（功能介绍、快速开始） |
| `GETTING_STARTED.md` | 开发者快速开始指南（详细环境搭建） |
| `docs/FAQ.md` | 常见问题解答（25个常见问题） |
| `docs/GLOSSARY.md` | 术语表（专业术语和缩写） |

### 开发规范
| 文档 | 说明 |
|------|------|
| `CLAUDE.md` | 本文件 - 快速参考和关键约束 |
| `CONTRIBUTING.md` | 贡献者指南（如何参与项目） |
| `.agents/CHECKLIST.md` | 执行前详细检查清单（服务重启完整流程） |
| `.agents/ERRORS.md` | 完整约束清单和历史纠错记录 |

### 部署与配置
| 文档 | 说明 |
|------|------|
| `.agents/DEPLOYMENT.md` | 快速部署指南（环境搭建、服务启停） |
| `.agents/CONFIG_GUIDE.md` | 配置管理说明（环境变量、多环境配置） |
| `migrations/README.md` | 数据库迁移指南 |

### 项目文档
| 文档 | 说明 |
|------|------|
| `CHANGELOG.md` | 项目更新日志（版本变更记录） |
| `docs/API_CHANGELOG.md` | API变更日志（接口变更历史） |
| `docs/API_EXAMPLES.md` | API使用示例（cURL/Python/TS） |
| `docs/ARCHITECTURE_DIAGRAMS.md` | 架构图（系统架构、ER图） |
| `docs/REQUIREMENTS.md` | 需求规格说明书（功能需求、非功能需求） |
| `docs/OPTIMIZATION_PLAN.md` | 项目优化方案（架构评分、优化路线图） |
| `docs/DEPRECATIONS.md` | 弃用说明（API变更、迁移指南） |
| `docs/DOCUMENTATION_GUIDE.md` | 文档维护指南 |
| `docs/DOCUMENTATION_MAP.md` | 文档地图（完整文档导航） |

### 架构设计
| 文档 | 说明 |
|------|------|
| `backend/README.md` | 后端架构指南（FastAPI + SQLModel） |
| `frontend-v3/DESIGN_SYSTEM.md` | 前端设计系统（色彩、字体、组件规范） |
| `frontend-v3/docs/ARCHITECTURE.md` | 前端架构指南（Feature-based架构、测试架构） |

### 测试文档
| 文档 | 说明 |
|------|------|
| `.agents/TEST_GUIDE.md` | 完整测试指南（pytest + Vitest） |
| `tests/README.md` | 后端测试说明（测试结构、Fixtures） |
| `tests/e2e/README.md` | E2E测试说明（Playwright） |
