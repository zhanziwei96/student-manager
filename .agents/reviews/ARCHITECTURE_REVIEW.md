# 架构设计审查报告

> 审查时间：2026-03-26  
> **复查时间：2026-03-27**
> 审查者：架构设计 Agent  
> 项目：ClassHub 学生管理系统

---

## 📋 复查摘要（2026-03-27）

### 复查评分

| 模块 | 上次评分 | **当前评分** | 变化 |
|------|----------|--------------|------|
| **整体架构** | 7.8/10 | **8.5/10** | ⬆️ +0.7 |
| **分层合理性** | 8.0/10 | **8.5/10** | ⬆️ +0.5 |
| **依赖关系** | 8.5/10 | **9.0/10** | ⬆️ +0.5 |
| **配置管理** | 8.5/10 | **9.0/10** | ⬆️ +0.5 |
| **测试验证** | 8.5/10 | **8.5/10** | ➡️ 持平 |
| **综合评分** | **7.8/10** | **8.5/10** | ⬆️ **+0.7** |

### 关键改进
- ✅ **SEC-003安全加固完成** - bcrypt密码哈希，移除salt字段
- ✅ **领域事件模式落地** - 事件总线实现清晰
- ✅ **并发保护机制完善** - BE-008乐观锁保护
- ✅ **测试全部通过** - 101个测试验证架构稳健

### 遗留架构问题
- ⚠️ **ScoreLog重复记录风险** - CRUD层和事件处理器都创建记录
- ❌ **API层直接操作Session** - users.py违反分层原则
- ⚠️ **乐观锁无唯一约束** - 无法真正防止并发覆盖
- ⚠️ **API层跨层访问User模型** - students.py直接访问

### 架构亮点确认
1. ✅ 领域事件模式与事务边界清晰
2. ✅ 配置管理支持多环境
3. ✅ 安全加固（bcrypt + JWT + 限流）
4. ✅ 审计日志中间件不阻塞响应

---

> 以下是原始审查报告（2026-03-26）

---

## 总体评分：78/100

**一句话总结**：ClassHub 是一个架构设计良好、分层清晰的学生管理系统，采用现代化技术栈（FastAPI + Vue 3），在领域驱动设计和安全实践方面表现出色，但存在数据库选型局限、分布式场景支持不足等技术债务。

---

## 架构亮点（6个）

### 1. 领域事件模式与事务边界清晰

**位置**：`backend/app/core/events.py`, `backend/app/crud/student.py::update_student_score`

这是一个优秀的解耦设计。系统通过轻量级事件总线 (`EventBus`) 实现了领域事件的发布-订阅，将核心副作用（分数日志记录）与主业务逻辑分离。

**值得称赞的设计**：
- 使用 SQLAlchemy `after_commit` 事件确保事件只在事务成功后发布
- 避免了"事件处理成功但业务数据回滚"的不一致情况
- 为后续扩展（如通知、积分系统）预留了清晰的接入点

### 2. 乐观锁机制保障并发安全

**位置**：`backend/app/crud/student.py`, `backend/app/crud/user.py`

在学生分数更新和用户登录状态更新中实现了乐观锁（version 字段），并配合重试机制：

```python
for attempt in range(max_retries):
    session.refresh(user)  # 获取最新版本
    user.version += 1
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        continue  # 自动重试
```

这种设计避免了并发修改导致的数据覆盖问题，是并发控制的正确实践。

### 3. 前端状态管理的门面模式

**位置**：`frontend-v3/src/stores/auth.ts`, `frontend-v3/src/composables/useAuth.ts`

解决了 Pinia 与 TanStack Query 双重状态管理的常见问题：
- TanStack Query 作为服务端状态的单一数据源
- Pinia 作为门面 (Facade) 提供统一接口
- 保持了向后兼容性，同时避免了状态同步的复杂性

### 4. 审计日志的透明切面设计

**位置**：`backend/app/core/middleware.py`

通过中间件自动记录敏感操作，实现了横切关注点与业务逻辑的分离：
- 可配置的路由匹配规则（支持路径参数）
- 非阻塞的日志记录（try-except 保护）
- 自动从 JWT Cookie 解析用户信息

### 5. 统一的 API 响应处理

**位置**：`frontend-v3/src/lib/api.ts`, `backend/app/core/exceptions.py`

前后端配合实现了统一的错误响应格式 `{success, data, message}`：
- 前端拦截器自动处理 `res.success` 检查，简化调用代码
- 后端异常处理器统一转换 FastAPI 异常为标准格式
- 开发/生产环境差异化的错误信息展示

### 6. SQLModel 的现代化 ORM 实践

**位置**：`backend/app/models/`

使用 SQLModel 统一了 SQLAlchemy 的表模型和 Pydantic 的验证模型：
- 减少重复代码（无需单独的 Schema 类）
- 类型安全（IDE 支持更好）
- 与 FastAPI 生态深度集成

---

## 主要风险（按严重性排序）

| 等级 | 问题 | 位置 | 潜在后果 | 修复建议 |
|------|------|------|----------|----------|
| 🔴 高 | **SQLite 单文件数据库瓶颈** | `backend/app/core/db.py` | 无法水平扩展；并发写入性能受限；容器化部署时数据持久化复杂 | 评估迁移到 PostgreSQL；或实现读写分离（主从复制） |
| 🔴 高 | **内存限流器无分布式支持** | `backend/main.py::lifespan`, `login.py` | 多实例部署时限流失效；攻击者可绕过单个实例的限制 | 使用 Redis 实现分布式限流；或配置负载均衡器的速率限制 |
| 🟡 中 | **领域事件非持久化** | `backend/app/core/events.py` | 进程重启丢失未处理事件；事件处理器异常会导致数据不一致 | 实现持久化事件存储（如数据库表）；或引入消息队列（RabbitMQ/Celery） |
| 🟡 中 | **JWT Token 无法主动失效** | `backend/app/core/jwt.py` | 用户登出后 Token 仍有效直至过期；账号禁用后仍可访问 | 实现 Token 黑名单（Redis）；或使用 Refresh Token 机制 |
| 🟡 中 | **密码验证接口遗留旧代码** | `backend/app/api/routes/login.py::96,140` | 调用已弃用的 `verify_password_hash` 函数，传递不必要的 salt 参数 | 统一使用 `verify_password()` 函数；移除 salt 参数 |
| 🟢 低 | **审计日志可能阻塞响应** | `backend/app/core/middleware.py::_save_audit_log` | 数据库连接池耗尽时，审计日志记录会阻塞主请求 | 改为异步写入（后台任务队列）；或分离审计数据库 |
| 🟢 低 | **前端乐观更新未处理 409** | `frontend-v3/src/composables/useStudents.ts::useScoreUpdate` | 后端返回 409 冲突时，虽然回滚数据，但没有提示用户刷新 | 在 onError 中添加用户提示 toast |

---

## 深度分析

### 1. 数据库选型与扩展性风险

**现象**：系统使用 SQLite 作为生产数据库，虽然配置了 WAL 模式和连接池，但本质上仍是单文件数据库。

**根因**：
- 项目初期选择 SQLite 是为了简化部署
- WAL 模式确实提升了读性能，但写操作仍受限于文件锁
- 容器化场景下需要处理数据卷挂载

**影响**：
- **短期**：1000 以下用户量场景可正常运行
- **长期**：无法水平扩展；备份和迁移复杂；多副本部署时数据不一致

**方案**：
```python
# 1. 创建数据库抽象层，隐藏具体实现
# backend/app/core/db.py
from abc import ABC, abstractmethod

class Database(ABC):
    @abstractmethod
    def get_session(self): ...

# 2. 实现 SQLite 和 PostgreSQL 两种驱动
class SQLiteDB(Database): ...
class PostgresDB(Database): ...

# 3. 通过配置切换
def get_database() -> Database:
    if settings.database.url.startswith("postgresql"):
        return PostgresDB()
    return SQLiteDB()
```

### 2. 内存限流器的分布式缺陷

**现象**：登录限流使用 `pyrate_limiter` 的内存存储 (`InMemoryBucket`)，状态保存在单个进程的内存中。

**根因**：
- 简单部署场景下单机限流足够
- 未考虑多实例部署的横向扩展需求

**影响**：
- 攻击者可轮流请求不同实例，绕过限流
- 负载均衡器轮询场景下，限流效果降低为 1/N（N 为实例数）

**方案**：
```python
# 使用 Redis 作为限流存储
from pyrate_limiter import Limiter, RedisBucket

async def init_limiter():
    redis = await aioredis.create_redis_pool('redis://localhost')
    bucket = RedisBucket(redis, rates=[rate], key_prefix="rate_limit")
    return Limiter(bucket)
```

### 3. 密码验证接口的兼容性债务

**现象**：`login.py` 中仍调用已弃用的 `verify_password_hash(password, hash, salt)`，虽然函数内部忽略 salt，但接口设计存在误导。

**根因**：
- SEC-003 安全修复迁移不彻底
- 向后兼容的代码未清理

**影响**：
- 新开发者可能误解密码验证逻辑
- 代码中存在不必要的参数传递

**方案**：
```python
# 1. 清理 login.py 中的调用
# 修改前:
if not verify_password_hash(password, student.password_hash, student.salt):

# 修改后:
if not verify_password(password, student.password_hash):

# 2. 添加 deprecation warning 到旧函数
import warnings
def verify_password_hash(...):
    warnings.warn("Deprecated: use verify_password()", DeprecationWarning)
    return verify_password(password, password_hash)
```

---

## 重构路线图

### 立即执行（本周）
- [ ] **统一密码验证接口**：将 `verify_password_hash` 调用替换为 `verify_password`，移除 salt 参数传递
- [ ] **添加乐观更新冲突提示**：在 `useScoreUpdate` 的 `onError` 中添加 toast 提示用户"数据已被修改，请刷新"
- [ ] **文档化数据库限制**：在 README 中明确说明 SQLite 的并发限制和推荐的用户规模

### 短期（本月）
- [ ] **JWT Token 黑名单**：实现 Redis 存储的 Token 黑名单，在登出和修改密码时使旧 Token 失效
- [ ] **审计日志异步化**：使用 `BackgroundTask` 或线程池异步写入审计日志，避免阻塞主请求
- [ ] **引入数据库抽象层**：为后续迁移到 PostgreSQL 做准备，隐藏具体数据库实现

### 长期（季度）
- [ ] **数据库迁移评估**：评估迁移到 PostgreSQL 的成本，编写迁移脚本
- [ ] **分布式限流**：使用 Redis 实现跨实例的限流器
- [ ] **持久化事件总线**：实现基于数据库的事件存储，或引入消息队列支持
- [ ] **API 版本化**：为重大变更准备 `/api/v2/` 路由前缀策略

---

## 技术债务清单

| 优先级 | 债务项 | 文件位置 | 备注 |
|--------|--------|----------|------|
| P1 | 旧密码验证接口 | `login.py:96,140` | 需要清理 |
| P2 | 学生模型中的 salt 字段 | `models/student.py:27` | 标记为 DEPRECATED，可移除 |
| P2 | 用户模型中的 salt 字段 | `models/user.py:48` | 标记为 DEPRECATED，可移除 |
| P3 | 上传文件清理逻辑 | `routes/students.py:256-259` | 考虑使用上下文管理器 |
| P3 | 限流器异常静默 | `routes/login.py:60-61` | 限流检查失败时放行，需监控 |

---

## 架构决策记录

### ADR-001: 数据库选型
- **决策**：使用 SQLite 作为生产数据库
- **原因**：简化部署，单文件易于备份
- **后果**：并发写入受限，无法水平扩展
- **状态**：接受（计划迁移到 PostgreSQL）

### ADR-002: 认证机制
- **决策**：使用 JWT + HttpOnly Cookie
- **原因**：无状态、防 XSS、与 SPA 配合良好
- **后果**：Token 无法主动失效
- **状态**：接受（计划添加 Redis 黑名单）

### ADR-003: 限流策略
- **决策**：单机内存限流
- **原因**：简单部署，无需外部依赖
- **后果**：多实例部署时限流失效
- **状态**：接受（计划迁移到 Redis）

---

**审查完成时间**：2026-03-26  
**建议复查时间**：修复 P0 问题后
