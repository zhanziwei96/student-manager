# CLAUDE.md

---

**文档版本**: v2.0  
**最后更新**: 2026-04-14  
**适用版本**: v3.0.0+  
**状态**: ✅ 已同步代码

---

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

### 前端操作
- [ ] **修改 Vue/TS 文件后**: 已评估是否需要创建或修改测试，并已运行前端测试验证
- [ ] **Tailwind CSS v4**: 自定义 `@theme` 时保留 `--spacing: 0.25rem` 基础单位，或使用 `@theme inline`
- [ ] **API 响应处理**: 禁止直接访问 `res.xxx`，必须访问 `res.data.xxx`
- [ ] **TanStack Query / 缓存一致性**: 修改 queryKey 后同步检查所有 `invalidateQueries` 调用，保证跨文件一致
- [ ] **类型一致性**: JWT `sub`（字符串）与 API `id`（数字）比较前已统一转换（`Number()` / `String()`）
- [ ] **异步刷新顺序**: mutation 后需要刷新数据时，`await refetch()` 完成后再显示成功提示

### Read 工具强制预检（每次调用前必须执行）
- [ ] **参数检查**: 在 commentary 中显式输出一行确认（如：`Read preflight: limit=200, offset=1. OK.`）
  - `limit` 必须是正整数（> 0），禁止传负数
  - `offset` >= 1
  - 超大文件优先用 `Grep`，不盲目读全文
  - **未输出此行即调用 Read，视为违规**

### 通用操作
- [ ] **curl 命令**: 已添加 `--max-time 10` 或 `--connect-timeout 5` 超时
- [ ] **未经同意**: 不擅自修改功能或简化需求
- [ ] **禁止回退**: 碰到问题不回退组件版本，先尝试修复或报告
- [ ] **跨文件修改一致性**: 涉及多个文件的修改时，已搜索并确认所有相关引用（queryKey、常量、接口调用）同步更新

**完整约束详见**: [`.agents/CHECKLIST.md`](./.agents/CHECKLIST.md) 和 [`.agents/ERRORS.md`](./.agents/ERRORS.md)

---

本文档为 Claude Code (claude.ai/code) 提供本仓库的代码编写指南。
## 语言规范
- 所有对话和文档都使用中文
- 文档使用 markdown 格式

## 行为准则

以下为准则用于减少常见 LLM 编码失误，与项目特定指令合并使用。

### 1. 先思考再编码

**不要假设，不要隐藏困惑，要主动呈现权衡。**

- 实施前明确陈述假设；若不确定，主动提问。
- 当存在多种解释时，呈现它们，而不是默默选择。
- 若存在更简单的方法，应指出；必要时提出反对意见。
- 若某事不清楚，停下来，指出困惑点，然后提问。

### 2. 极简优先

**用最少代码解决问题，拒绝臆测。**

- 不添加未请求的功能。
- 不为一次性代码创建抽象。
- 不添加未被要求的"灵活性"或"可配置性"。
- 不对不可能发生的场景做错误处理。
- 若写了 200 行却能用 50 行完成，重写它。

### 3. 精准修改

**只碰必须修改的代码，只清理自己造成的残留。**

- 不"改进"相邻代码、注释或格式。
- 不重构没坏的东西。
- 匹配现有代码风格，即使你个人偏好不同。
- 若改动导致某些 import / 变量 / 函数变为无用，清理它们。
- 不删除预先存在的死代码，除非被明确要求。

### 4. 目标驱动执行

**定义成功标准，循环验证直到通过。**

- "添加验证" → "为无效输入写测试并使其通过"
- "修复 bug" → "写复现测试，再使其通过"
- "重构 X" → "确保重构前后测试均通过"

对于多步骤任务，简要列出计划：
```
1. [步骤] → 验证: [检查]
2. [步骤] → 验证: [检查]
3. [步骤] → 验证: [检查]
```

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
- **数据库**: PostgreSQL 15（开发=本地安装，生产=Docker 容器）

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

详细的前后端开发约束、通用禁令、测试约束和历史纠错记录，参见：
- [`.agents/ERRORS.md`](./.agents/ERRORS.md) — 执行约束清单和历史纠错记录
- [`.agents/CHECKLIST.md`](./.agents/CHECKLIST.md) — 执行前详细检查清单

以下仅列出最常用、最简短的速查项：

### 后端速查
- **API 响应常量**：使用 `ApiResponseConst.SUCCESS` / `DATA` / `MESSAGE`
- **环境变量格式**：使用双下划线，如 `DATABASE__PATH`
- **密码验证新接口**：`verify_password()` / `hash_password()`
- **JWT 时区**：`datetime.now(ZoneInfo("Asia/Shanghai"))`
- **限流状态码**：返回 `429`，禁止 `503`

### 前端速查
- **API 响应处理**：禁止 `res.user.role`，必须 `res.data.role`
- **Tailwind v4**：自定义 `@theme` 时保留 `--spacing: 0.25rem` 或使用 `@theme inline`
- **TanStack Query 缓存一致性**：修改 `queryKey` 时必须同步检查所有 `invalidateQueries`
- **类型一致性**：JWT `sub`（字符串）与 API `id`（数字）比较前统一转换
- **异步刷新顺序**：`await mutate(); await refetch(); showSuccess()`

### 测试速查
- **运行路径**：始终在项目根目录运行 `pytest tests/ -v`
- **修改后**：必须询问用户是否需要运行测试

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
| `.agents/ERRORS.md` | 执行约束清单和历史纠错记录 |

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
