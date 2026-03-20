# 班级管理系统 - FastAPI + DDD架构

## 架构概览

本项目采用 **FastAPI** + **DDD（领域驱动设计）** 架构，完全前后端分离。

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                          │
│                   http://localhost:3000                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                          │
│                   http://localhost:8000                     │
├─────────────────────────────────────────────────────────────┤
│  接口层 (Interface)                                          │
│  ├── 处理HTTP请求/响应 (FastAPI路由)                          │
│  ├── 输入验证 (Pydantic模型)                                  │
│  └── 调用应用服务                                             │
├─────────────────────────────────────────────────────────────┤
│  应用层 (Application)                                        │
│  ├── 应用服务 (协调用例)                                      │
│  ├── 事务控制                                                 │
│  └── DTO转换                                                  │
├─────────────────────────────────────────────────────────────┤
│  领域层 (Domain) ★ 核心                                      │
│  ├── 实体 (Student, User, Checkin)                           │
│  ├── 值对象 (StudentId, Score, Password)                     │
│  ├── 仓储接口                                                 │
│  └── 领域事件                                                 │
├─────────────────────────────────────────────────────────────┤
│  基础设施层 (Infrastructure)                                 │
│  ├── 数据库访问 (SQLite)                                     │
│  ├── 仓储实现                                                 │
│  ├── 限流器 (FastAPI-Limiter)                               │
│  └── Session管理                                             │
└─────────────────────────────────────────────────────────────┘
```

## 技术栈

- **框架**: FastAPI 0.104+
- **ASGI服务器**: Uvicorn
- **数据验证**: Pydantic v2
- **限流**: FastAPI-Limiter + fakeredis (内存存储)
- **Session**: Starlette SessionMiddleware
- **数据库**: SQLite3

## 目录结构

```
backend/
├── domain/                      # 领域层（核心业务逻辑）
│   ├── entities/               # 实体
│   │   ├── student.py
│   │   ├── user.py
│   │   ├── checkin.py
│   │   └── score_log.py
│   ├── value_objects/          # 值对象
│   │   ├── student_id.py
│   │   ├── score.py
│   │   └── password.py
│   ├── repositories/           # 仓储接口
│   │   ├── student_repository.py
│   │   ├── user_repository.py
│   │   └── checkin_repository.py
│   └── events/                 # 领域事件
│       ├── score_changed.py
│       └── student_checked_in.py
├── application/                 # 应用层（用例协调）
│   ├── services/               # 应用服务
│   │   ├── student_app_service.py
│   │   ├── user_app_service.py
│   │   ├── checkin_app_service.py
│   │   └── privacy_service.py
│   └── dto/                    # 数据传输对象
│       ├── student_dto.py
│       └── user_dto.py
├── infrastructure/              # 基础设施层
│   ├── persistence/            # 持久化
│   │   ├── database.py
│   │   └── repositories/       # 仓储实现
│   │       ├── sqlite_student_repository.py
│   │       ├── sqlite_user_repository.py
│   │       ├── sqlite_checkin_repository.py
│   │       └── sqlite_score_log_repository.py
│   └── security/               # 安全
│       ├── rate_limiter.py     # 限流器
│       └── session.py          # Session工具
├── interface/                   # 接口层
│   └── api/                    # REST API控制器
│       ├── student_controller.py
│       ├── user_controller.py
│       ├── checkin_controller.py
│       └── class_session_controller.py
├── main.py                      # FastAPI应用入口
├── requirements.txt             # 依赖
└── start.sh                     # 启动脚本
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动后端

```bash
# 方式1: 使用启动脚本
./start.sh

# 方式2: 直接使用 uvicorn
uvicorn main:app --reload --port 8000

# 方式3: 使用 python
python main.py
```

后端将在 http://localhost:8000 运行

### 3. 启动前端

```bash
cd frontend
pnpm install  # 或 npm install
pnpm dev      # 或 npm run dev
```

前端将在 http://localhost:3000 运行

## API文档

FastAPI自动生成API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API接口列表

### 学生管理
- `GET /api/students` - 获取学生列表
- `GET /api/students/{student_id}` - 获取单个学生
- `POST /api/students` - 创建学生
- `POST /api/students/{student_id}/score` - 更新分数
- `DELETE /api/students/{student_id}` - 删除学生
- `POST /api/students/import` - Excel导入

### 签到系统
- `POST /api/checkin` - 学生签到
- `POST /api/teacher-checkin` - 老师代签
- `GET /api/checkin/records` - 签到记录
- `GET /api/checkin/stats` - 签到统计
- `GET /api/checkin/today` - 今日签到

### 用户管理
- `POST /api/login` - 用户登录
- `POST /api/logout` - 用户登出
- `GET /api/me` - 当前用户信息
- `POST /api/change-password` - 修改密码

### 管理员
- `GET /api/admin/users` - 用户列表
- `POST /api/admin/users` - 创建用户
- `PUT /api/admin/users/{user_id}` - 更新用户
- `DELETE /api/admin/users/{user_id}` - 删除用户
- `POST /api/admin/users/{user_id}/reset-password` - 重置密码
- `POST /api/admin/users/{user_id}/unlock` - 解锁账号
- `POST /api/admin/reset-scores` - 重置所有分数

### 课堂会话
- `GET /api/class-session` - 获取当前课堂状态
- `POST /api/class-session` - 设置/结束课堂
- `GET /api/class-session/students` - 课堂学生签到状态

### 其他
- `GET /api/stats` - 统计数据
- `GET /api/score/logs` - 分数变更日志

## 限流配置

使用 FastAPI-Limiter 实现限流，存储在内存中（fakeredis）：

| 接口 | 限制 |
|------|------|
| 登录 | 5次/分钟 |
| 签到 | 10次/分钟 |
| 分数修改 | 10次/分钟 |
| 其他 | 60次/分钟 |

## 环境变量

```bash
# 会话密钥（生产环境必须设置）
export SECRET_KEY="your-secret-key-here"

# 开发/生产模式
export FASTAPI_ENV="development"  # 或 "production"
```

## 与Flask版本对比

| 特性 | Flask版本 | FastAPI版本 |
|------|-----------|-------------|
| 框架 | Flask 3.x | FastAPI 0.104+ |
| 自动文档 | ❌ | ✅ Swagger/ReDoc |
| 数据验证 | 手动 | Pydantic自动验证 |
| 异步支持 | ❌ | ✅ |
| 性能 | 一般 | 高（基于Starlette） |
| 类型提示 | 部分 | 完整 |

## DDD架构优势

1. **业务逻辑集中**: 领域层包含核心业务规则
2. **可测试性高**: 领域层可独立单元测试
3. **可维护性好**: 清晰的边界和职责分离
4. **易于扩展**: 添加新功能只需新增领域实体

## 开发指南

### 添加新API

1. **定义领域实体**（domain/entities/）
2. **定义仓储接口**（domain/repositories/）
3. **实现仓储**（infrastructure/persistence/repositories/）
4. **创建应用服务**（application/services/）
5. **创建API控制器**（interface/api/）
6. **注册路由**（main.py）

### 示例

```python
# interface/api/example_controller.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api", tags=["example"])

@router.get("/example")
async def example():
    return {"success": True, "data": []}

# main.py
from interface.api import example_controller
app.include_router(example_controller.router)
```
