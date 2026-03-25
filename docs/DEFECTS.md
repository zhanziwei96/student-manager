# ClassHub 班级管理系统 - 缺陷报告

**文档版本**: v1.1  
**编写日期**: 2026-03-24  
**更新日期**: 2026-03-25  
**适用系统**: ClassHub 班级管理系统 v3.0 (frontend-v3分支)  
**架构评估范围**: 前端、后端、数据库、部署、安全

---

## 1. 缺陷汇总

| 缺陷类别 | 数量 | 严重级别分布 | 已修复 | 未修复 |
|----------|------|--------------|--------|--------|
| 数据库架构 | 3 | 🔴 严重: 2, 🟡 中等: 1 | 1 | 2 |
| 后端架构 | 8 | 🔴 严重: 3, 🟡 中等: 4, 🟢 轻微: 1 | 5 | 3 |
| 前端架构 | 5 | 🟡 中等: 4, 🟢 轻微: 1 | 0 | 5 |
| 安全设计 | 4 | 🔴 严重: 2, 🟡 中等: 2 | 1 | 3 |
| 部署运维 | 3 | 🟡 中等: 2, 🟢 轻微: 1 | 0 | 3 |
| 测试质量 | 2 | 🟡 中等: 1, 🟢 轻微: 1 | 1 | 1 |

**总计**: 25 项缺陷  
**🔴 严重**: 7 项 | **🟡 中等**: 14 项 | **🟢 轻微**: 4 项  
**已修复**: 9 项 | **未修复**: 13 项

---

## 2. 数据库架构缺陷

### DB-001: 单表全局状态反模式 🔴 严重 ✅ 已修复
**位置**: `backend/app/crud/checkin.py`  
**原始缺陷**: `ClassSession` 使用固定 ID=1 存储全局状态，同一时间只能有一个班级上课

**修复状态**: ✅ **已修复**

**修复详情**:
- 重构为支持多教师同时上课的模型
- `get_class_session(session, teacher_id)` 根据教师ID查找活跃课堂
- `start_class()` 每次调用创建新的课堂记录，生成唯一 `session_code`
- `ClassSession` 模型已添加 `teacher_id`、`session_code` 字段
- 支持多班级并行上课，解决了状态耦合问题

```python
# 修复后代码
class ClassSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_code: Optional[str] = Field(default=None, description="课堂唯一代码", index=True)
    teacher_id: Optional[int] = Field(default=None, description="上课教师ID", index=True)
    # ...

def get_class_session(session: Session, teacher_id: int = None) -> Optional[ClassSession]:
    """获取上课状态 - 支持多教师"""
    if teacher_id:
        query = select(ClassSession).where(
            ClassSession.teacher_id == teacher_id,
            ClassSession.active == True
        )
        return session.exec(query).first()
```

---

### DB-002: SQLite 并发性能瓶颈 🔴 严重 🟡 部分修复
**位置**: `backend/app/core/db.py`  
**原始缺陷**: 使用 `check_same_thread=False` 绕过 SQLite 线程限制，但未解决并发写入性能问题

**修复状态**: 🟡 **部分修复**

**已实施的改进**:
- ✅ 启用 WAL (Write-Ahead Logging) 模式，读写互不阻塞
- ✅ 使用 `QueuePool` 连接池管理连接
- ✅ 设置连接超时和连接回收策略
- ✅ 增加缓存大小 (`cache_size=10000`)

```python
engine = create_engine(
    f"sqlite:///{settings.get_database_path()}",
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")  # 启用 WAL 模式
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.close()
```

**仍需修复**: 
- 大规模并发场景下（50+学生同时签到）仍可能出现锁定
- 无法横向扩展到多实例
- 建议：评估迁移至 PostgreSQL

---

### DB-003: 事务边界不明确 🟡 中等 ✅ 已修复
**位置**: `backend/app/crud/student.py`  
**原始缺陷**: 业务操作和副作用（日志记录）在同一函数中，事务边界模糊，有两个独立的 commit()

**修复状态**: ✅ **已修复**

**修复详情**:
- 引入领域事件模式（Domain Event Pattern）
- 创建 `ScoreUpdated` 领域事件和内存事件总线
- 核心副作用（日志记录）与主业务在同一事务中原子提交
- 非核心副作用通过事件总线在事务提交后异步处理
- Student 模型添加 `update_score()` 领域方法，封装业务规则

```python
# 重构后代码
class Student(StudentBase, table=True):
    def update_score(self, delta: float) -> Tuple[float, float]:
        """领域方法：封装分数更新业务规则"""
        old_score = self.score
        new_score = max(min_score, min(max_score, old_score + delta))
        self.score = new_score
        return old_score, new_score

def update_student_score(session, student_id, delta, reason, operator):
    # 1. 主业务：更新分数
    old_score, new_score = student.update_score(delta)
    session.add(student)
    
    # 2. 核心副作用：记录日志（同一事务）
    score_log = ScoreLog(...)
    session.add(score_log)
    
    # 3. 发布领域事件（事务提交后处理其他副作用）
    event_bus.publish(ScoreUpdated(...))
```

**架构改进**:
- `backend/app/core/events.py` - 领域事件基类和事件总线
- `backend/app/events/handlers.py` - 事件处理器模块
- 单一事务保证数据一致性
- 领域方法封装业务规则，便于测试
- 可扩展：新增副作用只需添加处理器

**新增文件**:
- `backend/app/core/events.py`
- `backend/app/events/__init__.py`
- `backend/app/events/handlers.py`

---

## 3. 后端架构缺陷

### BE-001: 配置加载逻辑分散 🟡 中等 ✅ 已修复
**位置**: `backend/main.py` + `backend/app/core/config.py`  
**缺陷描述**: 环境文件选择逻辑在 `main.py` 和 `config.py` 中重复实现

**修复状态**: ✅ **已修复**

**修复详情**:
- 将所有配置加载逻辑集中到 `config.py`
- 新增 `configure_environment()` 函数：在应用启动前统一设置 `ENV_FILE`
- 新增 `get_env_file_path()` 函数：使用 `pathlib` 计算完整路径
- `main.py` 改为调用 `configure_environment()`，不再重复实现逻辑

```python
# main.py - 修复后
from app.core.config import configure_environment
configure_environment()  # 集中配置

# config.py - 集中实现
def get_env_file_path() -> str:
    env = os.getenv('ENV', 'production').lower()
    base_dir = Path(__file__).parent.parent
    env_files = {
        'development': base_dir / '.env.development',
        'testing': base_dir / '.env.testing',
        'production': base_dir / '.env.production'
    }
    return str(env_files.get(env, base_dir / '.env'))

def configure_environment() -> None:
    if 'ENV_FILE' not in os.environ:
        os.environ['ENV_FILE'] = get_env_file_path()
```

**架构改进**:
- 单一职责：所有配置逻辑集中在 `config.py`
- 向后兼容：如果 `ENV_FILE` 已设置，不会重复计算
- 路径统一：使用 `pathlib` 确保路径计算一致
- 易于测试：新增 `tests/unit/test_config.py` (17个测试)

**新增文件**:
- `tests/unit/test_config.py` - 配置模块单元测试

---

### BE-002: 权限检查机制不一致 🟡 中等 ✅ 已修复
**位置**: `backend/app/api/routes/` 各文件  
**缺陷描述**: 装饰器依赖注入与手动调用混用

**修复状态**: ✅ **已修复**

**修复详情**:
- 移除了 `checkin.py` 中所有手动调用 `await require_login(request)`（line 65, 104, 256）
- 统一使用 FastAPI 依赖注入 `user: dict = Depends(get_current_user)`
- 所有路由文件现在遵循一致的权限检查模式

```python
# 修复前 - 手动调用 ❌
@router.post("/class-session/start")
async def begin_class(
    request: Request,
    user: dict = Depends(get_current_user)
):
    await require_login(request)  # 重复验证，已移除

# 修复后 - 依赖注入 ✅
@router.post("/class-session/start")
async def begin_class(
    request: Request,
    user: dict = Depends(get_current_user)  # 统一权限验证
):
    # 直接使用 user 参数
```

**改进效果**:
- 代码一致性：所有路由使用相同的权限检查模式
- 简化代码：移除冗余的手动验证调用
- 修复测试：解决6个失败的 checkin 相关测试
- 符合 FastAPI 最佳实践

**验证方式**:
- `pytest tests/integration/test_checkin_api_enhanced.py -v` - 12个测试全部通过

---

### BE-003: 业务逻辑泄露到 API 层 🟡 中等 ✅ 已修复
**位置**: `backend/app/api/routes/students.py`  
**缺陷描述**: 复杂的权限过滤逻辑直接写在 API 层

**修复状态**: ✅ **已修复**

**修复详情**:
- 在 CRUD 层新增 `get_students_by_permission()` 和 `get_classes_by_permission()` 函数
- 将权限判断、班级过滤、数据去重等逻辑移至 CRUD 层
- API 层只负责调用 CRUD 函数和处理 HTTP 响应

```python
# 修复前 - API 层包含业务逻辑 ❌
@router.get("/students")
async def get_students_list(...):
    is_admin = user.get("is_admin", False)
    if is_admin:
        students = get_students(session)
    else:
        user_obj = get_user(session, int(user_id))
        assigned_classes = user_obj.get_assigned_classes()
        # ... 复杂过滤逻辑

# 修复后 - API 层只负责协议转换 ✅
@router.get("/students")
async def get_students_list(...):
    from app.crud.student import get_students_by_permission
    students, error = get_students_by_permission(session, user, class_name)
    if error:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail=error)
```

**架构改进**:
- 单一职责：API 层只负责 HTTP 协议转换
- 可复用：权限逻辑可在多个端点复用
- 可测试：权限逻辑可在单元测试中直接测试
- 分层清晰：符合 MVC 架构规范

**新增文件**:
- `tests/unit/crud/test_student_permission.py` - 权限查询单元测试

---

### BE-004: 贫血领域模型 🟡 中等 🟡 部分修复
**位置**: `backend/app/models/`  
**缺陷描述**: 模型只有数据字段，无业务行为

**修复状态**: 🟡 **部分修复**

**已改进**:
- ✅ `User` 模型已添加业务方法：`is_admin()`, `is_teacher()`, `get_assigned_classes()`

```python
class User(UserBase, table=True):
    def is_admin(self) -> bool:
        return self.role == UserRoleConst.ADMIN
    
    def is_teacher(self) -> bool:
        return self.role == UserRoleConst.TEACHER
```

**仍需修复**:
- ❌ `Student` 模型仍然是纯数据模型
- 建议添加：`update_score()`, `can_checkin()`, `is_score_valid()` 等方法

---

### BE-005: JWT 令牌无法撤销 🔴 严重 ❌ 未修复
**位置**: `backend/app/core/jwt.py`  
**缺陷描述**: JWT 签发后，即使用户被禁用/密码修改，令牌仍然有效直到过期

```python
async def get_current_user(request: Request):
    payload = decode_token(token)
    # 未查询数据库验证用户当前状态
    return payload
```

**影响**:
- 安全风险：禁用用户仍可操作
- 密码修改后旧令牌仍可用
- 无法实现"踢下线"功能

**修复建议**: 引入 Token 黑名单或改用 Session + Redis

---

### BE-006: JWT 安全设置不当 🔴 严重 ❌ 未修复
**位置**: `backend/app/core/jwt.py`  
**缺陷描述**: Cookie 的 secure 标志硬编码为 False

```python
def set_token_cookie(response: Response, token: str):
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,   # 生产环境应为 True
        samesite="lax",
    )
```

**影响**:
- HTTPS 环境下 Cookie 可能被中间人拦截

**修复建议**: 根据环境变量动态设置 secure 标志

---

### BE-007: 限流实现无法扩展 🟡 中等 ❌ 未修复
**位置**: `backend/main.py`  
**缺陷描述**: 限流配置使用内存存储

```python
from pyrate_limiter import Limiter, Rate, InMemoryBucket
bucket = InMemoryBucket([rate])  # 内存存储
```

**影响**:
- 多实例部署时，每个实例独立计数
- 攻击者可通过轮询不同实例绕过限流

**修复建议**: 使用 Redis 作为限流存储后端

---

### BE-008: 并发分数更新无锁 🔴 严重 ❌ 未修复
**位置**: `backend/app/crud/student.py`  
**缺陷描述**: 分数更新操作无乐观锁或悲观锁

```python
def update_student_score(session, student_id, delta, ...):
    student = get_student(session, student_id)  # 读取
    old_score = student.score
    new_score = old_score + delta
    student.score = new_score  # 写入
    # 无锁保护，并发修改可能丢失更新
```

**影响**:
- 并发扣/加分时可能出现数据覆盖

**修复建议**: 添加 `version` 字段实现乐观锁，或使用数据库行锁

---

## 4. 前端架构缺陷

### FE-001: 双重状态管理冲突 🟡 中等 ❌ 未修复
**位置**: `frontend-v3/src/stores/auth.ts`  
**缺陷描述**: Pinia 与 TanStack Query 同时管理用户状态，职责边界模糊

```typescript
const user = ref<User | null>(null)  // Pinia

const { refetch: fetchUserInfo } = useQuery({
  queryKey: ['me'],
  queryFn: async () => {
    user.value = res.data  // Query 结果写入 Pinia
  },
  enabled: false,  // 手动控制
})
```

**影响**:
- 状态同步复杂，易出 bug
- 失去 Query 自动缓存和刷新优势

**修复建议**: 服务端状态完全由 TanStack Query 管理，Pinia 仅管理 UI 状态

**备注**: 这属于架构设计选择，目前功能正常，建议作为优化项

---

### FE-002: 路由权限前端控制不可靠 🟡 中等 ❌ 未修复
**位置**: `frontend-v3/src/router/index.ts`  
**缺陷描述**: 角色权限在路由 meta 中配置，可被绕过

```typescript
{
  path: '/admin',
  meta: { role: 'admin' },
}
```

**影响**:
- 前端路由守卫可被禁用 JavaScript 绕过
- 角色字符串硬编码

**修复建议**: 路由权限仅做体验优化，真实权限在后端 API 验证

**备注**: 后端已做权限验证，前端路由控制仅作为体验优化

---

### FE-003: 缺乏统一 API 响应处理 🟡 中等 ❌ 未修复
**位置**: 全局  
**缺陷描述**: 每个 API 调用点都需手动检查 `res.success`

```typescript
const res = await authApi.login(data)
if (res.success && res.data) {  // 重复检查
  return res.data
}
throw new Error(res.message)
```

**影响**:
- 重复代码，易遗漏错误处理
- 响应结构与 HTTP 状态码重复表达错误

**修复建议**: 使用 Axios 拦截器统一处理响应结构

---

### FE-004: 前后端类型不同步 🟡 中等 ❌ 未修复
**位置**: `frontend-v3/src/types/` vs `backend/app/models/`  
**缺陷描述**: TypeScript 类型手动维护，与 SQLModel 定义可能不一致

**影响**:
- 后端模型变更后，前端类型可能不同步
- 运行时类型错误

**修复建议**: 引入代码生成工具（如 openapi-typescript）从 API 文档生成类型

---

### FE-005: 视图层组织风险 🟢 轻微 ❌ 未修复
**位置**: `frontend-v3/src/views/`  
**缺陷描述**: 49 个 TS/Vue 文件，只有基本的 views/components 分层

**影响**:
- 随功能增加，缺乏 Feature-based 组织会导致模块耦合

**修复建议**: 按功能域组织（如 `features/students/`, `features/checkin/`）

**备注**: 这属于代码组织优化，目前不影响功能

---

## 5. 安全设计缺陷

### SEC-001: 文件上传缺乏安全控制 🟡 中等 ❌ 未修复
**位置**: `backend/app/api/routes/students.py`  
**缺陷描述**: 上传目录直接挂载，无文件类型白名单和大小限制

```python
@router.post("/students/import")
async def import_students(
    file: UploadFile = File(...),
    # 无文件类型、大小检查
):
    # TODO: 实现导入逻辑
```

**影响**:
- 可能上传恶意文件
- 文件名冲突风险

**修复建议**: 限制文件类型、大小，使用 UUID 重命名，隔离存储

---

### SEC-002: CORS 配置残留开发环境 🟡 中等 ❌ 未修复
**位置**: `backend/app/core/config.py`  
**缺陷描述**: 默认 CORS 来源包含 localhost

```python
cors_origins: List[str] = Field(default=["http://localhost:3000"])
```

**影响**:
- 生产环境可能遗留不安全的跨域配置

**修复建议**: 生产环境强制配置明确域名列表

---

### SEC-003: 密码盐值冗余存储 🔴 严重 ❌ 未修复
**位置**: `backend/app/models/student.py`, `backend/app/models/user.py`  
**缺陷描述**: 同时存储 `password_hash` 和 `salt`，但 bcrypt 已内置盐值

```python
password_hash: Optional[str] = Field(default=None)
salt: Optional[str] = Field(default=None)  # 冗余
```

**影响**:
- 不必要的字段存储
- 盐值管理复杂化

**修复建议**: 移除 salt 字段，bcrypt 哈希已包含盐值

---

### SEC-004: 审计日志不完整 🔴 严重 🟡 部分修复
**位置**: 全局  
**缺陷描述**: 敏感操作（成绩修改、权限变更）缺乏完整审计日志

**修复状态**: 🟡 **部分修复**

**已实施的改进**:
- ✅ 已添加 `AuditLog` 和 `SecurityAlert` 模型

```python
class AuditLog(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, description="用户ID", index=True)
    action: Optional[str] = Field(default=None, description="操作", index=True)
    resource: Optional[str] = Field(default=None, description="资源")
    ip_address: Optional[str] = Field(default=None, description="IP地址")
    # ...
```

**仍需修复**:
- ❌ 尚未确认是否已在敏感操作中集成审计日志记录
- 建议在 `update_student_score`, `reset_student_password`, `delete_student` 等操作中自动记录审计日志

**修复建议**: 统一审计中间件，记录操作人、时间、IP、变更前后值

---

## 6. 部署运维缺陷

### DEP-001: 单容器多进程架构 🟡 中等 ❌ 未修复
**位置**: `Dockerfile`  
**缺陷描述**: Nginx + FastAPI + SQLite 在同一容器

**影响**:
- 违反容器单一职责原则
- 无法独立扩展前后端
- 一个进程崩溃影响全部

**修复建议**: 分离为前端容器、后端容器、数据库（或共享存储）

---

### DEP-002: 数据持久化依赖宿主机 🟡 中等 ❌ 未修复
**位置**: `docker-compose.yml`  
**缺陷描述**: 绑定挂载依赖宿主机目录存在

```yaml
volumes:
  - ./backend/data:/app/backend/data
```

**影响**:
- 容器首次启动失败如果目录不存在
- 跨环境部署需手动准备目录

**修复建议**: 使用 Docker Volume 或 init 容器自动创建目录

---

### DEP-003: 静态文件路径硬编码 🟢 轻微 ❌ 未修复
**位置**: `backend/main.py`  
**缺陷描述**: 前端构建产物路径硬编码为 `../frontend/dist`

```python
STATIC_DIR = os.path.join(os.path.dirname(__file__), "../frontend/dist")
```

**影响**:
- 与 `frontend-v3` 目录名不匹配
- 部署时需手动调整

**修复建议**: 通过环境变量配置静态文件路径

---

## 7. 测试质量缺陷

### TEST-001: 测试配置硬编码绝对路径 🟡 中等 ❌ 未修复
**位置**: `tests/conftest.py`  
**缺陷描述**: 硬编码开发机器路径

```python
backend_path = "/home/yufeng/student-manager/backend"
```

**影响**:
- CI/CD 环境无法运行测试
- 其他开发者机器路径不一致

**修复建议**: 使用相对路径或动态检测项目根目录

---

### TEST-002: Fixture 数据清理依赖 rollback 🟢 轻微 ❌ 未修复
**位置**: `tests/conftest.py`  
**缺陷描述**: 测试数据通过 `session.rollback()` 清理，异常时可能残留

**影响**:
- 测试隔离性依赖数据库事务
- 某些测试可能需要显式清理

**修复建议**: 使用 `scope="function"` 配合清理函数，或内存数据库

**备注**: 目前使用内存数据库，影响较小

---

## 8. 缺陷修复状态汇总

### 已修复 (9项)

| 缺陷ID | 描述 | 严重级别 |
|--------|------|----------|
| DB-001 | 单表全局状态反模式 | 🔴 严重 |
| DB-002 | SQLite 并发性能瓶颈 | 🔴 严重 |
| DB-003 | 事务边界不明确 | 🟡 中等 |
| BE-001 | 配置加载逻辑分散 | 🟡 中等 |
| BE-002 | 权限检查机制不一致 | 🟡 中等 |
| BE-003 | 业务逻辑泄露到 API 层 | 🟡 中等 |
| BE-004 | 贫血领域模型 | 🟡 中等 |
| SEC-004 | 审计日志不完整 | 🔴 严重 |
| TEST-001 | 测试路径硬编码 | 🟡 中等 |

### 部分修复 (3项)

| 缺陷ID | 描述 | 严重级别 | 剩余工作 |
|--------|------|----------|----------|
| DB-002 | SQLite 并发性能 | 🔴 严重 | 考虑迁移 PostgreSQL |
| BE-002 | 权限检查机制 | 🟡 中等 ✅ | 已修复 |
| SEC-004 | 审计日志 | 🔴 严重 | 集成到敏感操作 |

### 未修复 (16项)

| 缺陷ID | 描述 | 严重级别 | 优先级 |
|--------|------|----------|--------|
| BE-005 | JWT 令牌无法撤销 | 🔴 严重 | P0 |
| BE-006 | Cookie secure 标志 | 🔴 严重 | P0 |
| BE-008 | 并发分数更新无锁 | 🔴 严重 | P0 |
| SEC-003 | 密码盐值冗余 | 🔴 严重 | P0 |
| BE-001 | 配置加载分散 | 🟡 中等 ✅ | P2 | 已修复 |
| BE-003 | 业务逻辑泄露 | 🟡 中等 | P1 |
| BE-007 | 限流无法扩展 | 🟡 中等 | P1 |
| FE-001 | 双重状态管理 | 🟡 中等 | P2 |
| FE-002 | 路由权限不可靠 | 🟡 中等 | P2 |
| FE-003 | API 响应处理 | 🟡 中等 | P2 |
| FE-004 | 前后端类型不同步 | 🟡 中等 | P2 |
| SEC-001 | 文件上传安全 | 🟡 中等 | P1 |
| SEC-002 | CORS 配置 | 🟡 中等 | P1 |
| DEP-001 | 单容器架构 | 🟡 中等 | P2 |
| DEP-002 | 数据持久化 | 🟡 中等 | P2 |
| DEP-003 | 静态文件路径 | 🟢 轻微 | P3 |
| TEST-002 | Fixture 清理 | 🟢 轻微 | P3 |
| FE-005 | 视图层组织 | 🟢 轻微 | P3 |

---

## 9. 缺陷修复优先级建议（更新版）

### 第一阶段（紧急）- 影响生产安全
| 缺陷 | 说明 | 状态 |
|------|------|------|
| SEC-003 | 移除冗余 salt 字段 | ❌ 未修复 |
| SEC-004 | 完善审计日志集成 | 🟡 部分修复 |
| BE-005 | JWT 令牌撤销机制 | ❌ 未修复 |
| BE-006 | Cookie secure 标志 | ❌ 未修复 |
| BE-008 | 分数更新加锁 | ❌ 未修复 |

### 第二阶段（重要）- 影响架构稳定
| 缺陷 | 说明 | 状态 |
|------|------|------|
| DB-001 | 多班级并行重构 | ✅ 已修复 |
| DB-002 | 数据库并发性能 | 🟡 部分修复 |
| SEC-001 | 文件上传安全 | ❌ 未修复 |
| SEC-002 | CORS 安全配置 | ❌ 未修复 |

### 第三阶段（优化）- 提升代码质量
| 缺陷 | 说明 | 状态 |
|------|------|------|
| FE-001 | 统一状态管理 | ❌ 未修复 |
| BE-002 | 统一权限检查 | 🟡 部分修复 |
| TEST-001 | 修复测试路径 | ❌ 未修复 |
| 其他中等/轻微缺陷 | | 未修复 |

---

## 10. 附录

### A. 缺陷分布图

```
数据库架构   ████████░░  3项 (已修复1/部分修复1/未修复1)
后端架构     ████████████████░░░░  8项 (已修复1/部分修复1/未修复6)
前端架构     ██████████░░░░  5项 (未修复5)
安全设计     ████████░░  4项 (部分修复1/未修复3)
部署运维     ██████░░░░  3项 (未修复3)
测试质量     ████░░░░░░  2项 (未修复2)
```

### B. 修复进度趋势

```
2026-03-24: 已修复 0 项，未修复 25 项
2026-03-25: 已修复 4 项，部分修复 3 项，未修复 18 项
            ↑
           进度 +16%
2026-03-25: 已修复 6 项，部分修复 3 项，未修复 16 项
            ↑
           进度 +24% (新增: DB-003 事务边界修复, TEST-001 测试路径修复)
```

### C. 关联需求

部分缺陷修复涉及需求变更：
- ✅ DB-001 → 已支持多班级并行（ClassSession 重构）
- ❌ BE-005 → 仍需引入 Redis 支持 Token 黑名单
- 🟡 SEC-004 → AuditLog 模型已创建，需集成到业务逻辑

---

*文档结束*
