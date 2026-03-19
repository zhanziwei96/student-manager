# 班级管理系统 - DDD架构版本

## 架构概览

本项目采用领域驱动设计（DDD）架构，完全前后端分离。

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                          │
│                   http://localhost:3000                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端 (Flask)                            │
│                   http://localhost:5000                     │
├─────────────────────────────────────────────────────────────┤
│  接口层 (Interface)                                          │
│  ├── 处理HTTP请求/响应                                        │
│  ├── 输入验证                                                 │
│  └── 调用应用服务                                             │
├─────────────────────────────────────────────────────────────┤
│  应用层 (Application)                                        │
│  ├── 应用服务 (协调用例)                                      │
│  ├── 事务控制                                                 │
│  └── DTO转换                                                  │
├─────────────────────────────────────────────────────────────┤
│  领域层 (Domain) ★ 核心                                      │
│  ├── 实体 (Student, User)                                    │
│  ├── 值对象 (StudentId, Score, Password)                     │
│  ├── 仓储接口                                                 │
│  └── 领域事件                                                 │
├─────────────────────────────────────────────────────────────┤
│  基础设施层 (Infrastructure)                                 │
│  ├── 数据库访问 (SQLite)                                     │
│  ├── 仓储实现                                                 │
│  └── 安全配置                                                 │
└─────────────────────────────────────────────────────────────┘
```

## 目录结构

```
backend_ddd/
├── domain/                      # 领域层（核心业务逻辑）
│   ├── entities/               # 实体
│   │   ├── student.py
│   │   └── user.py
│   ├── value_objects/          # 值对象
│   │   ├── student_id.py
│   │   ├── score.py
│   │   └── password.py
│   ├── repositories/           # 仓储接口
│   │   ├── student_repository.py
│   │   └── user_repository.py
│   └── events/                 # 领域事件
│       ├── score_changed.py
│       └── student_checked_in.py
├── application/                 # 应用层（用例协调）
│   ├── services/               # 应用服务
│   │   ├── student_app_service.py
│   │   └── user_app_service.py
│   └── dto/                    # 数据传输对象
│       ├── student_dto.py
│       └── user_dto.py
├── infrastructure/              # 基础设施层
│   ├── persistence/            # 持久化
│   │   ├── database.py
│   │   └── repositories/       # 仓储实现
│   │       ├── sqlite_student_repository.py
│   │       └── sqlite_user_repository.py
│   └── config/                 # 配置
├── interface/                   # 接口层
│   └── api/                    # REST API控制器
│       ├── student_controller.py
│       └── user_controller.py
└── main.py                      # 应用入口
```

## 启动方法

### 1. 启动后端（DDD架构）

```bash
cd backend_ddd
export SECRET_KEY=$(openssl rand -hex 32)
python main.py
```

后端将在 http://localhost:5000 运行

### 2. 启动前端

```bash
cd frontend
pnpm install  # 如果还未安装依赖
pnpm dev
```

前端将在 http://localhost:3000 运行

## API接口

### 学生管理
- `GET /api/students` - 获取学生列表
- `GET /api/students/<student_id>` - 获取单个学生
- `POST /api/students` - 创建学生
- `POST /api/students/<student_id>/score` - 更新分数
- `DELETE /api/students/<student_id>` - 删除学生

### 用户管理
- `POST /api/login` - 用户登录
- `POST /api/logout` - 用户登出
- `GET /api/admin/users` - 获取所有用户
- `POST /api/admin/users` - 创建用户
- `PUT /api/admin/users/<id>` - 更新用户
- `DELETE /api/admin/users/<id>` - 删除用户
- `POST /api/admin/users/<id>/reset-password` - 重置密码
- `POST /api/admin/users/<id>/unlock` - 解锁账号

## 与传统架构对比

| 特性 | 传统架构 | DDD架构 |
|------|---------|---------|
| 代码组织 | 按技术分层 | 按业务领域 |
| 业务逻辑 | 分散在各处 | 集中在领域层 |
| 可测试性 | 依赖数据库 | 领域层可独立测试 |
| 可维护性 | 中等 | 高 |
| 开发效率 | 快（小项目） | 前期慢，后期快 |
| 扩展性 | 一般 | 好 |

## 领域模型设计

### 学生（Student）实体
- 唯一标识：StudentId（学号）
- 属性：姓名、班级、分数
- 行为：修改分数、签到

### 用户（User）实体
- 唯一标识：用户名
- 属性：姓名、角色、班级绑定
- 行为：登录、锁定/解锁、权限检查

### 值对象
- **StudentId**: 学号，不可变
- **Score**: 分数，范围0-100，有业务规则
- **Password**: 密码，存储哈希值

## 测试

```bash
# 测试登录
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 获取学生列表
curl http://localhost:5000/api/students \
  -b cookies.txt
```
