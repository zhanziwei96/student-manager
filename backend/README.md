# ClassHub 后端 - FastAPI + SQLModel 架构

> **最后更新时间**: 2026-04-13  
> **文档版本**: v3.0.1  
> **架构评分**: 8.5/10 🟢

## 架构概览

本项目采用 **FastAPI** + **SQLModel** 架构，完全前后端分离。

```
┌─────────────────────────────────────────────────────────────┐
│                     前端 (Vue 3 + TypeScript)                │
│                   http://localhost:5173                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                          │
│                   http://localhost:8000                     │
├─────────────────────────────────────────────────────────────┤
│  API 层 (app/api/)                                           │
│  ├── 路由定义 (FastAPI APIRouter)                            │
│  ├── 请求/响应模型 (Pydantic)                                │
│  ├── 依赖注入 (deps.py)                                      │
│  └── 权限控制 (JWT-based)                                    │
├─────────────────────────────────────────────────────────────┤
│  核心层 (app/core/)                                          │
│  ├── 配置管理 (Pydantic Settings)                            │
│  ├── 数据库连接 (SQLModel/SQLAlchemy)                        │
│  ├── 安全工具 (bcrypt密码哈希、JWT认证)                     │
│  ├── 领域事件 (events.py + handlers.py)                      │
│  └── 异常处理                                                │
├─────────────────────────────────────────────────────────────┤
│  CRUD 层 (app/crud/)                                         │
│  ├── 学生数据操作                                            │
│  ├── 用户数据操作                                            │
│  ├── 签到记录操作                                            │
│  ├── 审计日志操作                                            │
│  └── 乐观锁保护 (BE-008)                                     │
├─────────────────────────────────────────────────────────────┤
│  模型层 (app/models/)                                        │
│  ├── SQLModel 数据模型                                       │
│  ├── 业务常量定义                                            │
│  └── 枚举类型                                                │
└─────────────────────────────────────────────────────────────┘
```

## 技术栈

- **框架**: FastAPI 0.135+
- **ASGI服务器**: Uvicorn
- **ORM**: SQLModel 0.0.37 (SQLAlchemy + Pydantic)
- **数据库**: PostgreSQL 15
- **认证**: JWT + HttpOnly Cookie（python-jose）
- **密码哈希**: bcrypt（SEC-003已修复）
- **配置**: Pydantic Settings
- **限流**: 内存存储（pyrate-limiter）
- **架构模式**: 领域事件、乐观锁、依赖注入

## 目录结构

```
backend/
├── app/                         # 应用主目录
│   ├── api/                     # API 层
│   │   ├── __init__.py
│   │   ├── deps.py             # 依赖注入（权限、Session）
│   │   ├── middleware.py       # 审计日志中间件
│   │   └── routes/             # 路由处理器
│   │       ├── login.py        # 登录/认证
│   │       ├── students.py     # 学生管理
│   │       ├── users.py        # 用户管理（管理员）
│   │       ├── checkin.py      # 签到系统
│   │       ├── schedules.py    # 课程表管理
│   │       └── system.py       # 系统接口
│   ├── core/                    # 核心层
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic 配置
│   │   ├── db.py               # 数据库连接
│   │   ├── security.py         # 安全工具（bcrypt）
│   │   ├── exceptions.py       # 异常处理
│   │   ├── events.py           # 领域事件发布
│   │   └── logging.py          # 日志配置
│   ├── crud/                    # CRUD 操作
│   │   ├── __init__.py
│   │   ├── student.py          # 学生操作（含乐观锁）
│   │   ├── user.py             # 用户操作（含乐观锁）
│   │   ├── checkin.py          # 签到操作
│   │   └── audit.py            # 审计日志
│   ├── events/                  # 领域事件处理器
│   │   ├── __init__.py
│   │   └── handlers.py         # 事件处理逻辑
│   └── models/                  # 数据模型
│       ├── __init__.py
│       ├── user.py             # 用户模型
│       ├── student.py          # 学生模型
│       ├── checkin.py          # 签到模型
│       ├── audit.py            # 审计模型
│       └── constants.py        # 常量定义
├── data/                        # （历史残留目录，PostgreSQL 时代不再使用）
├── main.py                      # 应用入口
└── requirements.txt             # 依赖
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动后端

```bash
# 方式1: 直接使用 uvicorn（开发模式，支持热重载）
ENV=development uvicorn main:app --reload --port 8000

# 方式2: 使用 python（生产模式）
ENV=production python main.py
```

后端将在 http://localhost:8000 运行

### 3. 启动前端

```bash
cd frontend-v3  # 新版前端
pnpm install
pnpm dev
```

前端将在 http://localhost:5173 运行

## API 文档

FastAPI 自动生成 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 设计规范

### RESTful 接口规范

| 方法 | 用途 | 示例 |
|------|------|------|
| GET | 获取资源 | `GET /api/v1/students` |
| POST | 创建资源 | `POST /api/v1/students` |
| PUT | 更新资源 | `PUT /api/v1/students/{id}/score` |
| DELETE | 删除资源 | `DELETE /api/v1/students/{id}` |

### 统一响应格式

```json
// 成功
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}

// 失败
{
  "success": false,
  "message": "错误信息"
}
```

**注意**: 前端必须通过 `res.data` 访问数据，不能直接访问 `res.xxx`。

### 接口列表

#### 系统
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| GET | `/api/v1/stats` | 系统统计（需登录） |
| GET | `/api/v1/dashboard` | 仪表盘数据（公开，脱敏） |
| GET | `/api/v1/audit/logs` | 审计日志（管理员） |

#### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/login` | 用户登录（限流5次/分钟） |
| POST | `/api/v1/logout` | 用户登出 |
| GET | `/api/v1/me` | 当前用户信息 |
| POST | `/api/v1/change-password` | 修改密码 |

#### 学生管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/students` | 获取学生列表 |
| POST | `/api/v1/students` | 添加学生 |
| PUT | `/api/v1/students/{student_id}/score` | 更新分数（限流10次/分钟，乐观锁保护） |
| DELETE | `/api/v1/students/{student_id}` | 删除学生 |
| GET | `/api/v1/students/{student_id}/scores` | 分数历史 |
| PUT | `/api/v1/students/{student_id}/reset-password` | 重置密码（管理员） |
| POST | `/api/v1/students/import` | Excel 导入 |

#### 班级
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/classes` | 获取班级列表 |

#### 用户管理（管理员）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/admin/users` | 用户列表 |
| POST | `/api/v1/admin/users` | 创建用户 |
| PUT | `/api/v1/admin/users/{user_id}` | 更新用户 |
| PUT | `/api/v1/admin/users/{user_id}/reset-password` | 重置密码 |
| DELETE | `/api/v1/admin/users/{user_id}` | 删除用户 |

#### 课堂管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/class-session` | 获取当前课堂状态 |
| POST | `/api/v1/class-session/start` | 开始上课 |
| POST | `/api/v1/class-session/end` | 结束上课 |

#### 签到系统
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/checkin` | 学生签到（限流10次/分钟） |
| POST | `/api/v1/teacher-checkin` | 教师代签 |
| GET | `/api/v1/checkin/records` | 签到记录查询 |
| GET | `/api/v1/checkins/today` | 今日签到列表 |
| GET | `/api/v1/checkins/stats` | 签到统计 |

#### 课程表
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/schedules` | 获取课程表 |
| POST | `/api/v1/schedules` | 创建课程（管理员） |
| POST | `/api/v1/schedules/import` | 导入课程表 |
| GET | `/api/v1/schedules/today` | 获取今日课表 |

## 架构模式

### 1. 领域事件模式

```python
# 发布事件
from app.core.events import publish_event

publish_event(ScoreChangedEvent(
    student_id=student_id,
    old_score=old_score,
    new_score=new_score,
    changed_by=teacher_id
))

# 事件处理（app/events/handlers.py）
@register_handler(ScoreChangedEvent)
def handle_score_changed(event: ScoreChangedEvent):
    # 创建ScoreLog、发送通知等
    ...
```

### 2. 乐观锁保护（BE-008）

```python
# 模型定义
class Student(SQLModel, table=True):
    id: int = Field(primary_key=True)
    score: int = Field(default=0)
    version: int = Field(default=0)  # 乐观锁版本号

# CRUD层使用
from app.crud.student import update_student_score

update_student_score(
    session=session,
    student_id=student_id,
    score_change=10,
    changed_by=teacher_id
)
# 并发冲突自动抛出ConcurrentUpdateError
```

### 3. 依赖注入

```python
from fastapi import Depends, APIRouter
from sqlmodel import Session
from app.core.db import get_session
from app.api.deps import require_teacher

router = APIRouter()

@router.put("/api/v1/students/{student_id}/score")
def update_score(
    student_id: int,
    score_data: ScoreUpdate,
    session: Session = Depends(get_session),
    teacher_id: int = Depends(require_teacher)
):
    # teacher_id 已通过JWT验证
    # session 已注入数据库会话
    ...
```

## 配置管理

使用 Pydantic Settings 管理配置，支持环境变量和 `.env` 文件：

```bash
# 环境
ENV=production  # 或 development, testing

# 数据库
DATABASE__PATH=./data/class_system.db

# 安全配置
SECURITY__SECRET_KEY=your-secret-key  # JWT 签名密钥
SECURITY__MAX_LOGIN_FAILURES=10       # 最大登录失败次数
SECURITY__LOCKOUT_DURATION_MINUTES=30 # 账号锁定时间

# JWT配置
JWT__ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24小时
JWT__ALGORITHM=HS256
JWT__COOKIE_NAME=access_token

# 限流配置
RATE_LIMIT__ENABLED=true
RATE_LIMIT__LOGIN_MAX_REQUESTS=5
RATE_LIMIT__CHECKIN_MAX_REQUESTS=10
```

详见 [配置指南](../.agents/CONFIG_GUIDE.md)

## 开发指南

### 添加新 API

1. **定义 SQLModel 模型**（如需要）：`app/models/`
2. **添加 CRUD 操作**（如需要）：`app/crud/`
3. **创建路由**：`app/api/routes/`
4. **注册路由**：`main.py`

### 示例

```python
# app/api/routes/example.py
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.db import get_session
from app.api.deps import require_login

router = APIRouter(prefix="/api", tags=["example"])

@router.get("/example")
def example(
    request: Request,
    session: Session = Depends(get_session)
):
    user_id = require_login(request)
    return {"success": True, "data": []}

# main.py
from app.api.routes import example
app.include_router(example.router)
```

### 数据库操作示例

```python
# app/crud/example.py
from sqlmodel import Session
from app.models import Example

def create_example(session: Session, name: str) -> Example:
    example = Example(name=name)
    session.add(example)
    session.commit()
    session.refresh(example)
    return example
```

## 环境变量

```bash
# 会话密钥（生产环境必须设置）
export SECURITY__SECRET_KEY="your-secret-key-here-min-32-chars"

# 开发/生产模式
export ENV="production"  # 或 "development"

# 数据库路径
export DATABASE__PATH="/path/to/class_system.db"

# CORS 配置（开发环境）
export SECURITY__CORS_ORIGINS='["http://localhost:5173"]'
```

## 安全特性

| 特性 | 状态 | 说明 |
|------|------|------|
| bcrypt密码哈希 | ✅ 已实施 | SEC-003已修复，自动处理盐值 |
| JWT认证 | ✅ 已实施 | HttpOnly Cookie存储 |
| 乐观锁保护 | ✅ 已完善 | BE-008并发保护 |
| 请求限流 | ✅ 已实施 | 内存存储，无需Redis |
| 审计日志 | ✅ 已实施 | 敏感操作记录 |
| CORS配置 | ✅ 已实施 | 跨域安全策略 |
| 登录失败保护 | ✅ 已实施 | 10次失败后锁定30分钟 |

## 测试

```bash
# 运行全部测试
pytest tests/ -v

# 仅单元测试
pytest tests/unit -v

# 仅集成测试
pytest tests/integration -v

# 并发保护测试（BE-008）
pytest tests/unit/crud/test_concurrent_*.py -v
```

测试覆盖率：89%（467 个测试全部通过）

## 架构特点

1. **简洁分层**: API → CRUD → Models → Core，职责清晰
2. **类型安全**: 全代码类型提示，Pydantic 自动验证
3. **统一响应**: 标准化 API 响应格式
4. **配置灵活**: 环境变量 + `.env` 文件支持
5. **易于测试**: SQLModel 支持内存数据库，测试隔离
6. **前后端分离**: 前端位于 `frontend-v3/` 目录，独立部署
7. **领域事件**: 业务逻辑解耦，可扩展性强
8. **乐观锁**: 并发数据保护，防止数据竞争

## 已知问题

| 优先级 | 问题 | 位置 | 状态 |
|--------|------|------|------|
| 🟡 P1 | API层直接操作Session | `users.py:112-114` | 📋 待优化 |
| 🟡 P1 | 审计日志同步写入 | `middleware.py:128-137` | 📋 待优化（考虑异步化审计日志写入） |

### 已修复问题

| 问题 | 修复时间 | 修复方案 |
|------|----------|----------|
| ScoreLog重复记录 | 2026-04-01 | CRUD层仅发布事件，事件处理器统一创建记录 |
| SEC-006 审计日志系统 | 2026-04-05 | 审计日志中间件记录所有敏感操作 |

## 相关文档

- [执行前检查清单](../.agents/CHECKLIST.md)
- [配置管理指南](../.agents/CONFIG_GUIDE.md)
- [部署指南](../.agents/DEPLOYMENT.md)
- [常见错误速查](../.agents/ERRORS.md)
- [测试指南](../tests/README.md)
- [优化方案](../docs/OPTIMIZATION_PLAN.md)
- [需求规格](../docs/REQUIREMENTS.md)
- [弃用说明](../docs/DEPRECATIONS.md)

---

**架构评分**: 8.5/10 🟢  
**最后更新**: 2026-04-13（更新SEC-006审计日志状态、课程表接口完善、接口列表同步）
