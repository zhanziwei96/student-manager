# CLAUDE.md

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
pytest tests/ -v                    # 全部测试（约340个）
pytest tests/unit -v                # 仅单元测试
pytest tests/integration -v         # 仅集成测试
pytest tests/unit/test_jwt.py -v    # 单个测试文件

# 前端测试（在 frontend-v3/ 目录运行）
cd frontend-v3
pnpm test:run                       # 运行所有测试（58个）
pnpm test                           # 交互式测试模式
```

### 环境要求

- **Python**: 3.11+，使用 Conda 环境 `student-manage`
- **Node.js**: 20+，使用 pnpm 8+
- **数据库**: SQLite，位于 `backend/data/class_system.db`

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
├── components/    # UI 组件（ui/ + common/）
├── composables/   # Vue 组合式函数（useToast 是全局的）
├── features/      # 特性化模块
├── stores/        # Pinia 状态管理
├── router/        # Vue Router 配置
├── views/         # 页面级组件
└── types/         # TypeScript 类型定义
```

**关键模式：**
- Tailwind CSS v4 自定义主题：背景色 `#030307`，主色 `#6366f1`
- 自定义 `@theme` 时必须保留 `--spacing: 0.25rem` 或使用 `@theme inline`
- API 响应：后端返回 `{success, data, message}` 格式，通过 `res.data.xxx` 访问
- 使用 `@tanstack/vue-query` 进行服务端状态管理和缓存
- HTTP 请求使用 `ofetch`
- 图标来自 `lucide-vue-next`

### 数据库

- SQLite 文件数据库，位于 `backend/data/class_system.db`
- 配置使用双下划线格式：`DATABASE__PATH`（不是单下划线）
- 查看实际路径：`python -c "from app.core.config import get_settings; print(get_settings().get_database_path())"`
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

**修改代码前，请先阅读 `.agents/ERRORS.md` 获取完整约束清单。**

主要禁令：
1. 重启服务前必须先检查状态（使用 `make status` 或 `curl`）
2. Python 命令必须使用 Conda 环境（`conda run -n student-manage`）
3. 修改后端代码后，检查并更新相关测试
4. 修改 Vue/TS 代码后，创建或修改测试
5. 未经用户明确同意，不得修改功能需求

**服务重启流程：**
```bash
# 1. 检查当前状态
curl -s http://localhost:8000/api/health
curl -s http://localhost:5173 > /dev/null && echo "前端运行中"

# 2. 如需重启，先停止并等待
pkill -f "python main.py" && sleep 3
pkill -f "pnpm dev" && sleep 2

# 3. 启动服务
# （按上方开发章节所示，在独立终端中运行）

# 4. 验证
curl -s http://localhost:8000/api/health
curl -s http://localhost:5173 > /dev/null && echo "前端运行中"
```

## 配置说明

环境变量配置在 `backend/.env` 文件中：
- `ENV=production|development|testing`
- `DATABASE__PATH`（必须使用双下划线）
- `SECURITY__SECRET_KEY`（必须使用双下划线）
- 更多选项参见 `backend/.env.example`

## 文档索引

- `.agents/AGENTS.md` - AI 助手快速参考
- `.agents/ERRORS.md` - 约束清单和错误历史
- `README.md` - 完整项目文档
- `frontend-v3/DESIGN_SYSTEM.md` - 前端设计系统
- `frontend-v3/docs/ARCHITECTURE.md` - 前端架构指南
