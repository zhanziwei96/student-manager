# ClassHub 架构图

---

**文档版本**: v1.0  
**最后更新**: 2026-04-03  
**适用版本**: v3.0.0+  
**状态**: ✅ 已同步代码

---

## 系统整体架构

```mermaid
graph TB
    subgraph Client["客户端"]
        Browser["浏览器"]
        Mobile["移动端"]
    end

    subgraph Frontend["前端 (Vue 3 + TypeScript)"]
        Router["Vue Router"]
        Pinia["Pinia Store"]
        Query["TanStack Query"]
        Components["UI Components"]
    end

    subgraph Backend["后端 (FastAPI + SQLModel)"]
        API["API Routes<br/>/api/v1/*"]
        Auth["JWT + RBAC<br/>认证授权"]
        CRUD["CRUD Layer"]
        Events["Domain Events"]
    end

    subgraph Data["数据层"]
        PostgreSQL[("PostgreSQL 15<br/>classhub")]
        Memory["内存缓存<br/>(限流/会话)"]
    end

    Browser -->|"HTTP/WebSocket"| Router
    Mobile -->|"HTTP"| Router
    Router --> Pinia
    Router --> Components
    Components --> Query
    Query -->|"REST API"| API

    API --> Auth
    Auth --> CRUD
    CRUD --> Events
    CRUD --> PostgreSQL
    API --> Memory
```

---

## 后端分层架构

```mermaid
flowchart TB
    subgraph API_Layer["API Layer (api/)"]
        Routes["Routes<br/>/students, /checkin..."]
        Deps["Dependencies<br/>get_current_user"]
        Middleware["Middleware<br/>审计/限流"]
    end

    subgraph Business_Layer["Business Layer"]
        Events_Pub["Event Publisher"]
        Handlers["Event Handlers"]
    end

    subgraph Data_Layer["Data Layer (crud/)"]
        StudentCRUD["Student CRUD"]
        UserCRUD["User CRUD"]
        CheckinCRUD["Checkin CRUD"]
    end

    subgraph Core["Core (core/)"]
        Config["Config<br/>Pydantic Settings"]
        Security["Security<br/>JWT/bcrypt"]
        DB["Database<br/>SQLModel"]
    end

    Routes --> Deps
    Routes --> Middleware
    Routes --> Events_Pub
    Events_Pub --> Handlers
    Routes --> StudentCRUD
    Routes --> UserCRUD
    Routes --> CheckinCRUD
    StudentCRUD --> DB
    UserCRUD --> DB
    CheckinCRUD --> DB
    Deps --> Security
    Security --> Config
    DB --> Config
```

---

## 数据库 ER 图

```mermaid
erDiagram
    USER ||--o{ SCORE_LOG : "操作记录"
    USER ||--o{ CHECKIN_RECORD : "签到记录"
    USER ||--o{ AUDIT_LOG : "审计记录"
    STUDENT ||--o{ SCORE_LOG : "分数变更"
    STUDENT ||--o{ CHECKIN_RECORD : "签到"
    CLASS ||--o{ STUDENT : "包含"
    CLASS ||--o{ COURSE_SCHEDULE : "课程安排"
    USER ||--o{ COURSE_SCHEDULE : "授课"

    USER {
        int id PK
        string username UK
        string password_hash
        string name
        string role
        string assigned_class
        boolean is_active
        int login_fail_count
        datetime locked_until
        datetime last_login
        string last_login_ip
        int version
        datetime created_at
    }

    STUDENT {
        int id PK
        string student_id UK
        string name
        string class_name
        float score
        string password_hash
        boolean is_active
        datetime last_login
        int version
        datetime created_at
    }

    SCORE_LOG {
        int id PK
        int student_id FK
        int user_id FK
        float old_score
        float new_score
        float delta
        string reason
        string operator
        datetime created_at
    }

    CHECKIN_RECORD {
        int id PK
        int student_id FK
        int user_id FK
        string student_name
        string class_name
        string checkin_type
        datetime checkin_time
        string device_fingerprint
        string ip_address
        date checkin_date
    }

    CLASS {
        string name PK
        string description
        int student_count
        datetime created_at
    }

    COURSE_SCHEDULE {
        int id PK
        string class_name FK
        int teacher_id FK
        string course_name
        string day_of_week
        string start_time
        string end_time
        string classroom
        int week_type
    }

    AUDIT_LOG {
        int id PK
        int user_id FK
        string action
        string resource_type
        string resource_id
        string details
        string ip_address
        datetime created_at
    }
```

---

## 认证流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant API as API Routes
    participant Auth as JWT认证
    participant CRUD as CRUD层
    participant DB as 数据库

    Client->>API: POST /api/v1/login<br/>{username, password, role}
    API->>CRUD: 验证用户名/密码
    CRUD->>DB: 查询用户
    DB-->>CRUD: 用户信息
    CRUD-->>API: 验证结果

    alt 验证成功
        API->>Auth: 生成JWT Token
        Auth-->>API: access_token
        API->>API: 设置HttpOnly Cookie
        API-->>Client: 200 OK<br/>Set-Cookie: access_token=...
    else 验证失败
        API->>CRUD: 记录登录失败
        API-->>Client: 401 Unauthorized
    end

    Note over Client,DB: 后续请求
    Client->>API: GET /api/v1/students<br/>Cookie: access_token=...
    API->>Auth: 验证Token
    Auth-->>API: 用户claims
    API->>Auth: 检查权限(RBAC)
    Auth-->>API: 权限结果

    alt 权限通过
        API->>CRUD: 查询数据
        CRUD->>DB: SQL查询
        DB-->>CRUD: 结果
        CRUD-->>API: 数据
        API-->>Client: 200 OK + 数据
    else 权限不足
        API-->>Client: 403 Forbidden
    end
```

---

## 分数更新流程（乐观锁）

```mermaid
sequenceDiagram
    participant T1 as 线程1 (教师A)
    participant T2 as 线程2 (教师B)
    participant API as API层
    participant CRUD as CRUD层
    participant Events as 事件系统
    participant DB as 数据库

    Note over T1,DB: 并发分数更新场景

    T1->>API: 更新学生分数 (score=80, version=1)
    T2->>API: 同时更新同一学生 (score=85, version=1)

    API->>CRUD: update_student_score(id, score=80, version=1)
    API->>CRUD: update_student_score(id, score=85, version=1)

    CRUD->>DB: SELECT * WHERE id=1 AND version=1
    DB-->>CRUD: 学生数据 (version=1)

    CRUD->>DB: UPDATE score=80, version=2 WHERE version=1
    DB-->>CRUD: 更新成功

    CRUD->>Events: 发布 ScoreChangedEvent

    CRUD->>DB: UPDATE score=85, version=2 WHERE version=1
    DB-->>CRUD: 0行更新 (version已变为2)

    CRUD-->>API: 抛出 ConcurrentUpdateError
    API-->>T2: 409 Conflict<br/>"数据已被修改，请刷新后重试"

    Events->>DB: 创建 ScoreLog 记录
    API-->>T1: 200 OK<br/>更新成功
```

---

## 前端状态管理

```mermaid
flowchart TB
    subgraph Server["服务端状态"]
        TanStack["TanStack Query"]
        Cache["Query Cache"]
        ServerState["学生/签到/分数数据"]
    end

    subgraph ClientState["客户端状态"]
        Pinia["Pinia Store"]
        AuthStore["Auth Store<br/>用户信息/Token"]
        UIStore["UI Store<br/>Toast/Dialog状态"]
    end

    subgraph Components["UI组件"]
        Views["Views<br/>页面级组件"]
        UIComponents["UI Components<br/>Button/Card/Dialog"]
    end

    subgraph API_Client["API客户端"]
        HTTP["ofetch<br/>HTTP请求"]
        Interceptors["拦截器<br/>Token/错误处理"]
    end

    Views -->|"useQuery"| TanStack
    Views -->|"useStore"| Pinia
    UIComponents -->|"useToast"| UIStore

    TanStack --> Cache
    Cache -->|"stale-while-revalidate"| ServerState
    TanStack -->|"fetch"| HTTP

    Pinia --> AuthStore
    Pinia --> UIStore
    AuthStore -->|"getToken"| Interceptors

    HTTP --> Interceptors
    Interceptors -->|"API请求"| Backend["后端API"]
```

---

## 部署架构

```mermaid
graph LR
    subgraph User["用户"]
        Browser["浏览器/手机"]
    end

    subgraph Server["服务器"]
        Nginx["Nginx<br/>反向代理"]

        subgraph Backend_Container["后端容器"]
            FastAPI["FastAPI<br/>Python 3.11"]
        end

        subgraph PostgreSQL_Container["数据库容器"]
            PostgreSQL[("PostgreSQL 15<br/>classhub")]
        end

        subgraph Frontend_Container["前端容器"]
            Vite["Vite Dev Server<br/>(开发)"]
            StaticFiles["静态文件<br/>(生产)"]
        end
    end

    Browser -->|"HTTP/HTTPS"| Nginx
    Nginx -->|"/api/*"| FastAPI
    Nginx -->|"/"| Frontend_Container

    FastAPI --> PostgreSQL
```

---

## 相关文档

- [后端架构](../backend/README.md) - 详细的后端架构说明
- [前端架构](../frontend-v3/docs/ARCHITECTURE.md) - 前端架构详情
- [优化方案](./OPTIMIZATION_PLAN.md) - 架构优化建议

---

**注意**: 以上图表使用 Mermaid 语法，支持在 GitHub、GitLab 等平台上直接渲染。
