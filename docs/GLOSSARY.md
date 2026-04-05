# ClassHub 术语表

---

**文档版本**: v1.0  
**最后更新**: 2026-04-05  
**适用版本**: v3.0.0+  
**状态**: ✅ 已同步代码

---

本文档定义 ClassHub 项目中使用的专业术语和缩写，确保团队沟通一致性。

---

## A

### API (Application Programming Interface)
应用程序编程接口。ClassHub 使用 RESTful API 进行前后端通信。

### 审计日志 (Audit Log)
记录系统中敏感操作的日志，包括操作人、时间、IP地址等信息。用于安全审计和问题追踪。

---

## B

### bcrypt
一种密码哈希算法，自动处理盐值，安全性高于传统 SHA256。ClassHub 使用 bcrypt 进行密码存储（SEC-003）。

### Backend
后端。指 FastAPI 构建的服务器端应用程序，位于 `backend/` 目录。

---

## C

### ClassHub
班级管理系统 (Class Management Hub) 的项目名称。

### CRUD
Create（创建）、Read（读取）、Update（更新）、Delete（删除）的缩写。指数据的基本操作。

### 课程表 (Course Schedule)
按周循环的排课计划，包含课程名称、时间、教室、任课教师等信息。

### 课堂会话 (Class Session)
单次上课的签到时间段。教师开始上课后，学生可以进行签到。

### Cookie
存储在客户端的小型数据片段。ClassHub 使用 HttpOnly Cookie 存储 JWT Token。

### CORS (Cross-Origin Resource Sharing)
跨域资源共享。允许前端应用从不同域名访问后端 API。

### Conda
Python 环境管理工具。ClassHub 使用 Conda 管理 Python 依赖环境。

---

## D

### 暗色优先 (Dark First)
前端设计原则，以深色系为主色调，减少视觉疲劳。

### 领域事件 (Domain Event)
业务领域发生的事件，用于模块间解耦。例如：ScoreChangedEvent（分数变更事件）。

### 依赖注入 (Dependency Injection)
设计模式，通过外部传入依赖而非内部创建。FastAPI 原生支持依赖注入。

---

## E

### E2E (End-to-End)
端到端测试。模拟真实用户操作，测试完整业务流程。

### ER 图 (Entity-Relationship Diagram)
实体关系图。描述数据库表之间的关系。

---

## F

### FastAPI
现代 Python Web 框架，基于 Starlette 和 Pydantic，支持异步处理。

### Feature-based Architecture
按功能域组织代码的架构方式，将相关代码放在同一目录下。

### Frontend
前端。指 Vue 3 + TypeScript 构建的客户端应用程序，位于 `frontend-v3/` 目录。

---

## G

### 玻璃拟态 (Glassmorphism)
设计风格，使用半透明背景和 backdrop-blur 效果创造层次感。

---

## H

### HttpOnly Cookie
设置了 HttpOnly 属性的 Cookie，无法通过 JavaScript 访问，提升安全性。

### 健康检查 (Health Check)
用于检测服务是否正常运行的接口，路径为 `/api/v1/health`。

---

## I

### ID (Identifier)
标识符。唯一标识某个资源的编号。

---

## J

### JWT (JSON Web Token)
JSON Web 令牌。用于用户认证的令牌格式，包含用户信息和签名。

---

## L

### 乐观锁 (Optimistic Locking)
并发控制机制。通过版本号检测数据是否被修改，防止并发更新导致的数据丢失（BE-008）。

### 限流 (Rate Limiting)
限制单位时间内的请求次数，防止滥用和攻击。

---

## M

### Migration
数据库迁移。用于升级或修改数据库结构的脚本。

### Middleware
中间件。处理请求和响应的组件，如审计日志中间件。

### Makefile
构建自动化工具配置文件，包含常用命令快捷方式。

---

## O

### ORM (Object-Relational Mapping)
对象关系映射。SQLModel 是 ClassHub 使用的 ORM 工具。

### ofetch
HTTP 请求库，前端用于 API 调用，是 fetch 的增强版。

---

## P

### Pagination
分页。将大量数据分成多页展示的技术。

### Pinia
Vue 3 的状态管理库，替代 Vuex。

### pnpm
Node.js 包管理工具，比 npm/yarn 更快、更节省磁盘空间。

### Pydantic
Python 数据验证库，用于请求/响应模型定义和配置管理。

---

## R

### RBAC (Role-Based Access Control)
基于角色的访问控制。ClassHub 使用 admin/teacher/student 三种角色。

### RESTful
Representational State Transfer。一种 API 设计风格，使用 HTTP 方法操作资源。

### 热重载 (Hot Reload)
开发时自动重新加载代码变更，无需手动重启服务。

---

## S

### Salt
盐值。密码学中用于增加哈希随机性的数据。bcrypt 自动处理盐值，无需单独存储。

### Session
会话。可以指课堂会话（Class Session）或用户会话（User Session）。

### SHA256
安全哈希算法。ClassHub 旧版本使用的密码哈希算法，已升级为 bcrypt。

### SQLModel
SQLModel 是 SQLAlchemy 和 Pydantic 的结合，提供 ORM 和数据验证功能。

### SQLite
轻量级关系型数据库。ClassHub 使用 SQLite 存储数据。

### SSR (Server-Side Rendering)
服务端渲染。Vue 3 支持的服务端渲染技术。

---

## T

### Tailwind CSS
原子化 CSS 框架。ClassHub 前端使用 Tailwind CSS v4。

### TanStack Query
服务端状态管理库（原 React Query），用于数据获取和缓存。

### Teleport
Vue 3 特性，将组件渲染到 DOM 的其他位置，避免 z-index 问题。

### Token
令牌。指 JWT Token 或访问令牌。

### TypeScript
JavaScript 的超集，提供静态类型检查。

---

## U

### UI (User Interface)
用户界面。指用户与系统交互的界面。

### UX (User Experience)
用户体验。指用户使用系统的整体感受。

---

## V

### Vue 3
渐进式 JavaScript 框架。ClassHub 前端使用 Vue 3.5+。

### Vite
前端构建工具，提供快速的开发服务器和优化的生产构建。

### Vitest
Vite 原生的测试框架，用于前端单元测试。

### 版本号 (Version)
软件版本标识。ClassHub 使用语义化版本（Semantic Versioning）。

---

## W

### Worktree
Git 工作树。用于在同一仓库中同时处理多个分支的技术。

---

## 常用缩写

| 缩写 | 全称 | 说明 |
|------|------|------|
| API | Application Programming Interface | 应用程序接口 |
| BE | Backend | 后端 |
| CRUD | Create, Read, Update, Delete | 增删改查 |
| DB | Database | 数据库 |
| ENV | Environment | 环境 |
| FE | Frontend | 前端 |
| HTTP | HyperText Transfer Protocol | 超文本传输协议 |
| IP | Internet Protocol | 互联网协议 |
| JWT | JSON Web Token | JSON 网络令牌 |
| ORM | Object-Relational Mapping | 对象关系映射 |
| RBAC | Role-Based Access Control | 基于角色的访问控制 |
| REST | Representational State Transfer | 表述性状态转移 |
| SQL | Structured Query Language | 结构化查询语言 |
| SSR | Server-Side Rendering | 服务端渲染 |
| TS | TypeScript | JavaScript 超集 |
| UI | User Interface | 用户界面 |
| URL | Uniform Resource Locator | 统一资源定位符 |
| UX | User Experience | 用户体验 |
| JWT | JSON Web Token | JSON 网络令牌 |

---

## 业务术语

### 平时成绩
由签到、作业、课堂表现等组成的综合性评分。

### 总评成绩
按权重计算的学期最终成绩。

### 一机一签
签到限制策略，每台设备每天只能签到一次。

### 代签
教师帮未带设备的学生进行签到操作。

### 班级数据隔离
教师只能查看和管理自己负责班级的数据。

---

## 技术术语

### 三层架构
API 层 → CRUD 层 → Models 层的分层架构。

### 依赖注入
通过参数传递依赖，而非在内部创建，便于测试和解耦。

### 领域驱动设计 (DDD)
以业务领域为核心的软件设计方法。

### 响应式编程
数据变化自动更新 UI 的编程范式。

### 类型安全
通过类型系统防止运行时类型错误。

---

## 相关文档

- [API 变更日志](./API_CHANGELOG.md) - API 变更记录
- [后端架构](../backend/README.md) - 后端技术架构
- [前端架构](../frontend-v3/docs/ARCHITECTURE.md) - 前端技术架构
- [设计系统](../frontend-v3/DESIGN_SYSTEM.md) - 前端设计规范

---

**文档版本**: v1.0  
**最后更新**: 2026-04-05
