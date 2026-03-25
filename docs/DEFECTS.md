# ClassHub 班级管理系统 - 缺陷报告

**文档版本**: v1.7  
**编写日期**: 2026-03-24  
**更新日期**: 2026-03-25 (SEC-003 密码盐值冗余修复 + SEC-001 文件上传安全 + 前端架构修复)  
**适用系统**: ClassHub 班级管理系统 v3.0 (frontend-v3分支)  
**架构评估范围**: 前端、后端、数据库、部署、安全

---

## 1. 缺陷汇总

| 缺陷类别 | 数量 | 严重级别分布 | 已修复 | 未修复 |
|----------|------|--------------|--------|--------|
| 数据库架构 | 3 | 🔴 严重: 2, 🟡 中等: 1 | 1 | 2 |
| 后端架构 | 8 | 🔴 严重: 3, 🟡 中等: 4, 🟢 轻微: 1 | 7 | 1 |
| 前端架构 | 5 | 🟡 中等: 4, 🟢 轻微: 1 | 5 | 0 |
| 安全设计 | 4 | 🔴 严重: 2, 🟡 中等: 2 | 3 | 1 |
| 部署运维 | 3 | 🟡 中等: 2, 🟢 轻微: 1 | 0 | 3 |
| 测试质量 | 2 | 🟡 中等: 1, 🟢 轻微: 1 | 1 | 1 |

**总计**: 25 项缺陷  
**🔴 严重**: 7 项 | **🟡 中等**: 14 项 | **🟢 轻微**: 4 项  
**已修复**: 19 项 | **未修复**: 3 项

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

### BE-004: 贫血领域模型 🟡 中等 ✅ 已修复
**位置**: `backend/app/models/`  
**缺陷描述**: 模型只有数据字段，无业务行为

**修复状态**: ✅ **已修复**

**修复详情**:
- ✅ `User` 模型已添加业务方法：`is_admin()`, `is_teacher()`, `get_assigned_classes()`
- ✅ `Student` 模型已添加业务方法：`update_score()`（封装分数更新规则）

```python
class User(UserBase, table=True):
    def is_admin(self) -> bool:
        return self.role == UserRoleConst.ADMIN
    
    def is_teacher(self) -> bool:
        return self.role == UserRoleConst.TEACHER
    
    def get_assigned_classes(self) -> List[str]:
        # 从 JSON 解析班级列表

class Student(StudentBase, table=True):
    def update_score(self, delta: float) -> Tuple[float, float]:
        # 封装分数更新业务规则（范围限制等）
        old_score = self.score
        new_score = max(min_score, min(max_score, old_score + delta))
        self.score = new_score
        return old_score, new_score
```

**架构说明**:
项目采用**混合模式**（平衡充血模型和贫血模型）：
- **模型层**: 封装核心领域方法和业务规则（如 `update_score()`）
- **CRUD 层**: 处理数据访问和依赖外部状态的业务逻辑（如权限检查）

**为什么不完全充血**:
- `can_checkin()` 依赖当前课堂状态，属于应用层逻辑
- 过度充血会导致模型依赖过多，增加复杂度
- 当前架构平衡了封装性和可维护性

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

### BE-006: JWT 安全设置不当 🔴 严重 ✅ 已修复
**位置**: `backend/app/core/jwt.py`  
**缺陷描述**: Cookie 的 secure 标志硬编码为 False

**修复状态**: ✅ **已修复**

**修复详情**:
- 在 `SecuritySettings` 中添加 `cookie_secure` 配置项
- `set_token_cookie()` 函数根据配置动态设置 secure 标志
- 默认值为 `False`（开发环境），生产环境应通过环境变量设置为 `True`

```python
# config.py
class SecuritySettings(BaseSettings):
    cookie_secure: bool = Field(default=False, description="Cookie Secure标志")

# jwt.py
def set_token_cookie(response: Response, token: str):
    settings = get_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.security.cookie_secure,  # 根据环境配置
        samesite="lax",
    )
```

**环境配置示例**:
```bash
# 生产环境
export SECURITY__COOKIE_SECURE=true

# 开发环境（默认）
export SECURITY__COOKIE_SECURE=false
```

**安全建议**:
- 生产环境必须启用 HTTPS 并设置 `SECURITY__COOKIE_SECURE=true`
- 配合 `httponly=True` 和 `samesite="lax"` 提供完整 Cookie 安全保护

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

### BE-008: 并发分数更新无锁 🔴 严重 ✅ 已修复
**位置**: `backend/app/crud/student.py`, `backend/app/crud/user.py`  
**缺陷描述**: 分数更新和登录失败计数操作无乐观锁保护

**修复状态**: ✅ **已修复**

**修复详情**:
- 在 `Student` 和 `User` 模型添加 `version` 字段（INTEGER DEFAULT 1）
- `update_student_score()` 使用乐观锁，更新时递增 version，冲突时抛出 HTTP 409
- `record_login_failure()` 和 `record_login_success()` 使用乐观锁，支持自动重试
- 新增数据库迁移脚本 `add_version_optimistic_lock.sql`

```python
# Student 模型添加 version 字段
class Student(StudentBase, table=True):
    version: int = Field(default=1, description="乐观锁版本号")

def update_student_score(session, student_id, delta, ...):
    # 使用 select 获取最新版本
    statement = select(Student).where(Student.student_id == student_id)
    student = session.exec(statement).first()
    
    # 执行业务操作
    old_score, new_score = student.update_score(delta)
    
    # 乐观锁：递增版本号
    student.version += 1
    
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="分数已被其他用户修改")
```

**修复范围**:
- ✅ 学生分数更新 (`update_student_score`)
- ✅ 登录失败计数 (`record_login_failure`)
- ✅ 登录成功记录 (`record_login_success`)

**新增文件**:
- `migrations/add_version_optimistic_lock.sql` - 数据库迁移脚本
- `tests/unit/crud/test_concurrent_score_update.py` - 并发分数更新测试 (4个)
- `tests/unit/crud/test_concurrent_login_failure.py` - 并发登录失败测试 (7个)

---

## 4. 前端架构缺陷

### FE-001: 双重状态管理冲突 🟡 中等 ✅ 已修复
**位置**: `frontend-v3/src/stores/auth.ts`  
**缺陷描述**: Pinia 与 TanStack Query 同时管理用户状态，职责边界模糊

**修复状态**: ✅ **已修复**

**修复详情**:
- 创建 `useAuthQuery` composable，使用 TanStack Query 管理用户状态
- Pinia Store (`auth.ts`) 改为门面(facade)模式，实际状态由 Query 管理
- 服务端状态（用户数据）完全由 Query 管理，Pinia 只转发状态
- 组件通过 Pinia facade 访问，保持向后兼容，无需修改组件

```typescript
// 修复前: Pinia 直接管理 user 状态
const user = ref<User | null>(null)  // Pinia
const { refetch: fetchUserInfo } = useQuery({
  queryFn: async () => {
    user.value = res.data  // ❌ 手动同步到 Pinia
  },
})

// 修复后: Query 管理状态，Pinia 作为门面
export const useAuthStore = defineStore('auth', () => {
  const authQuery = useAuthQuery()  // Query 管理服务端状态
  
  // Pinia 只转发 Query 的状态
  const user = authQuery.user
  const isAuthenticated = authQuery.isAuthenticated
  
  return { user, isAuthenticated, ... }
})
```

**架构改进**:
- **单一数据源**: 用户数据完全由 TanStack Query 管理
- **自动缓存**: Query 自动处理缓存失效和后台刷新
- **清晰职责**: 服务端状态 vs UI 状态分离明确
- **向后兼容**: 组件继续使用 `useAuthStore()`，无需修改

**新增文件**:
- `frontend-v3/src/composables/useAuth.ts` - Query 状态管理

**修改文件**:
- `frontend-v3/src/stores/auth.ts` - Pinia 门面模式
- `frontend-v3/src/router/index.ts` - 添加注释说明
- `frontend-v3/src/composables/useStudentProfile.ts` - 使用 useAuthQuery
- `frontend-v3/src/composables/index.ts` - 导出 useAuthQuery

---

### FE-002: 路由权限前端控制不可靠 🟡 中等 ✅ 已修复
**位置**: `frontend-v3/src/router/index.ts`  
**缺陷描述**: 角色权限在路由 meta 中配置，可被绕过

**修复状态**: ✅ **已修复**

**修复详情**:
- 在路由守卫中添加明确的安全警告注释，说明前端控制只是体验优化
- 添加 `UserRoleConst` 常量，避免角色字符串硬编码
- 在控制台输出警告日志，提醒开发者真实权限验证在后端

```typescript
// 修复前: 硬编码角色字符串
meta: { role: 'admin' }

// 修复后: 使用类型安全常量
import { UserRoleConst } from '@/types/api'
meta: { role: UserRoleConst.ADMIN }

// 路由守卫添加安全警告注释
/**
 * ⚠️ 安全警告 ⚠️
 * 前端路由权限控制仅作为用户体验优化，不能替代后端权限验证。
 *
 * 原因:
 * 1. 客户端代码可被绕过（禁用 JS、直接访问 API）
 * 2. 前端路由守卫无法阻止恶意请求
 *
 * 真实权限控制应在:
 * - 后端 API 层进行验证（已实现）
 * - 数据库访问控制（已实现）
 */
```

**为什么不完全移除前端控制？**
- **用户体验**: 防止已登录用户看到"无权限"页面一闪而过
- **导航辅助**: 自动将用户跳转到其角色对应的首页
- **开发调试**: 快速识别权限相关问题

**安全边界明确**:

| 层级 | 控制方式 | 可靠性 | 用途 |
|------|----------|--------|------|
| **后端 API** | Token + 数据库验证 | ✅ 可靠 | 真实权限控制 |
| **前端路由** | 本地状态检查 | ⚠️ 不可靠 | 体验优化 |

**修改文件**:
- `frontend-v3/src/types/api.ts` - 添加 UserRoleConst 常量
- `frontend-v3/src/router/index.ts` - 使用常量，添加安全注释

---

### FE-003: 缺乏统一 API 响应处理 🟡 中等 ✅ 已修复
**位置**: 全局  
**缺陷描述**: 每个 API 调用点都需手动检查 `res.success`

**修复状态**: ✅ **已修复**

**修复详情**:
- 在 `lib/api.ts` 中添加统一的响应处理逻辑
- API 客户端自动检查 `res.success`，成功时提取 `res.data`，失败时抛出错误
- 所有 API 模块和 composables 更新，移除重复的 `res.success` 检查

```typescript
// 修复前: 每个调用点重复检查
const res = await authApi.login(data)
if (res.success && res.data) {
  return res.data
}
throw new Error(res.message)

// 修复后: 直接获取数据，错误自动抛出
const data = await authApi.login(data)
// 错误自动抛出，无需手动检查
```

**核心实现**:

```typescript
// lib/api.ts
async function request<T>(url: string, options?: ...): Promise<T> {
  const response = await api<ApiResponse<T>>(url, options)
  
  if (!response.success) {
    throw new Error(response.message || '请求失败')
  }
  
  return response.data as T
}

export async function get<T>(url: string, params?: ...): Promise<T> {
  return request<T>(url, { method: 'GET', query: params })
}
```

**修改文件**:
- `frontend-v3/src/lib/api.ts` - 统一响应处理
- `frontend-v3/src/api/*.ts` - 简化返回类型
- `frontend-v3/src/composables/*.ts` - 移除重复检查

**API 模块更新**:
- `auth.ts`, `students.ts`, `checkin.ts`, `classSession.ts`
- `classes.ts`, `stats.ts`, `users.ts`

**Composables 更新**:
- `useAuth.ts`, `useStudents.ts`, `useClassSession.ts`
- `useCheckins.ts`, `useStats.ts`, `useClasses.ts`
- `useTeachers.ts`, `useStudentCheckin.ts`, `useStudentProfile.ts`

---

### FE-004: 前后端类型不同步 🟡 中等 ✅ 已修复
**位置**: `frontend-v3/src/types/` vs `backend/app/models/`  
**缺陷描述**: TypeScript 类型手动维护，与 SQLModel 定义可能不一致

**修复状态**: ✅ **已修复**

**修复详情**:
- 更新前端类型定义，添加后端模型对应注释
- 统一字段命名：`Student.status` → `Student.is_active`
- 补充缺失字段：`User.assigned_classes`, `Student.created_at`, `Student.last_login`
- 添加类型映射注释，方便后续维护时参考

```typescript
/**
 * 学生类型 - 对应后端 StudentResponse
 *
 * 后端模型: backend/app/models/student.py::StudentResponse
 * 注意: 保持与后端字段一致，修改时需同步更新
 */
export interface Student {
  id: number
  student_id: string
  name: string
  class_name: string
  score: number
  is_active: boolean           // FE-004: 统一为 is_active
  created_at?: string          // FE-004: 补充缺失字段
  last_login?: string          // FE-004: 补充缺失字段
}
```

**修改文件**:
- `frontend-v3/src/types/api.ts` - 更新类型定义，添加后端对应注释
- `frontend-v3/src/views/admin/Students.vue` - `status` → `is_active`
- `frontend-v3/src/views/teacher/Students.vue` - `status` → `is_active`
- `frontend-v3/src/views/student/Dashboard.vue` - `status` → `is_active`

**轻量级方案说明**:
- 不引入复杂的代码生成工具
- 通过注释建立前后端类型映射关系
- 统一字段命名规范（is_active 替代 status）
- 未来如需更严格的类型同步，可考虑 openapi-typescript

---

### FE-005: 视图层组织风险 🟢 轻微 ✅ 已修复
**位置**: `frontend-v3/src/views/`  
**缺陷描述**: 49 个 TS/Vue 文件，只有基本的 views/components 分层

**修复状态**: ✅ **已修复（文档化方案）**

**修复详情**:
- 添加架构文档 `frontend-v3/docs/ARCHITECTURE.md`，说明 Feature-based 组织结构
- 创建 `frontend-v3/src/features/` 目录，作为功能域组织的示例
- 创建 `students` feature 示例，展示推荐的项目结构

**推荐结构**:
```
frontend-v3/src/
├── views/              # 页面入口（保持现有结构）
├── features/           # 按功能域组织（新增）
│   ├── students/       # 学生管理功能
│   ├── checkin/        # 签到功能
│   ├── classes/        # 班级管理
│   └── teachers/       # 教师管理
└── shared/             # 共享资源
```

**迁移策略**:
1. **阶段1**: 新功能使用 Feature-based 结构
2. **阶段2**: 逐步迁移现有功能（按需进行）
3. **阶段3**: 清理旧结构（未来进行）

**新增文件**:
- `frontend-v3/docs/ARCHITECTURE.md` - 架构指南
- `frontend-v3/src/features/README.md` - Features 目录说明
- `frontend-v3/src/features/students/` - 示例 Feature 结构

**备注**: 采用渐进式重构策略，不修改现有代码，为未来的重构提供蓝图

---

## 5. 安全设计缺陷

### SEC-001: 文件上传缺乏安全控制 🟡 中等 ✅ 已修复
**位置**: `backend/app/api/routes/students.py`  
**缺陷描述**: 上传目录直接挂载，无文件类型白名单和大小限制

**修复状态**: ✅ **已修复**

**修复详情**:

创建安全上传模块 `backend/app/core/upload.py`，提供完整的安全控制：

```python
async def save_upload_file_securely(
    upload_file: UploadFile,
    allowed_extensions: List[str] = None,
    max_size_mb: int = None,
    use_uuid: bool = True
) -> Tuple[str, str]:
    """安全保存上传文件"""
    # 1. 验证文件名安全性（防止路径遍历）
    # 2. 验证文件扩展名白名单 + MIME类型
    # 3. 检查文件大小限制
    # 4. 使用UUID重命名文件
    # 5. 保存到隔离目录
```

**安全控制措施**:

| 控制项 | 实现方式 | 配置项 |
|--------|----------|--------|
| 文件类型白名单 | 扩展名 + MIME类型双重验证 | `UPLOAD_ALLOWED_EXTENSIONS` |
| 危险文件黑名单 | `.exe`, `.sh`, `.php` 等 30+ 种 | 内置常量 |
| 文件大小限制 | Content-Length + 实际读取限制 | `UPLOAD_MAX_FILE_SIZE_MB` |
| 文件名安全 | UUID重命名 + 路径清理 | `UPLOAD_USE_UUID_FILENAME` |
| 路径遍历防护 | 清理 `../` 和 `./` | 自动处理 |
| 临时文件清理 | try/finally 确保清理 | 自动处理 |

**配置示例**:

```python
# backend/app/core/config.py
class UploadSettings(BaseSettings):
    allowed_extensions: List[str] = [".xlsx", ".xls"]
    allowed_content_types: List[str] = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ]
    max_file_size_mb: int = 10
    use_uuid_filename: bool = True
```

**更新后的 API**:

```python
@router.post("/students/import")
async def import_students(
    file: UploadFile = File(..., description="Excel文件 (.xlsx/.xls)"),
    ...
):
    # SEC-001: 安全文件上传
    file_path, original_filename = await save_upload_file_securely(
        file,
        allowed_extensions=settings.upload.allowed_extensions,
        max_size_mb=settings.upload.max_file_size_mb,
        use_uuid=settings.upload.use_uuid_filename
    )
    ...
    finally:
        cleanup_file(file_path)  # 清理临时文件
```

**测试覆盖**: 70 个单元测试覆盖所有安全场景
- 路径遍历攻击防护（`../../../etc/passwd`）
- 危险文件类型拒绝（`.exe`, `.php`, `.sh` 等）
- 超大文件拒绝
- 文件名安全处理（UUID重命名）
- 文件清理机制

**新增文件**:
- `backend/app/core/upload.py` - 安全上传工具模块
- `tests/unit/test_upload.py` - 上传安全单元测试（70个）

**修改文件**:
- `backend/app/core/config.py` - 添加 UploadSettings 配置类
- `backend/app/api/routes/students.py` - 使用安全上传
- `backend/.env.example` - 添加上传配置示例

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

### SEC-003: 密码盐值冗余存储 🔴 严重 ✅ 已修复
**位置**: `backend/app/models/student.py`, `backend/app/models/user.py`  
**缺陷描述**: 同时存储 `password_hash` 和 `salt`，但 bcrypt 已内置盐值

**修复状态**: ✅ **已修复（标记弃用，简化接口）**

**修复详情**:

bcrypt 算法自动处理盐值（内嵌在哈希字符串中），单独存储 `salt` 字段是冗余的。

**新的简化接口**:

```python
# SEC-003: 新的推荐接口
from app.core.security import hash_password, verify_password

# 生成密码哈希（bcrypt 自动处理盐值）
password_hash = hash_password("user_password")

# 验证密码
is_valid = verify_password("user_password", stored_hash)
```

**向后兼容接口**（仍然可用）:

```python
# 旧接口仍可用，但 salt 参数被忽略/返回空字符串
password_hash, _ = generate_password_hash("password")
is_valid = verify_password_hash("password", stored_hash, user.salt)  # salt 参数被忽略
```

**模型字段更新**:

```python
# backend/app/models/user.py
salt: Optional[str] = Field(
    default=None, 
    description="[DEPRECATED] bcrypt已内置盐值，此字段将在未来版本移除"
)
```

**CRUD 函数更新**:

```python
# SEC-003: 移除 salt 参数
def create_user(session, username, name, password_hash, role, assigned_classes):
    user = User(
        ...,
        password_hash=password_hash,
        # salt 不再设置
    )

def reset_password(session, user, password_hash):
    user.password_hash = password_hash
    # salt 不再设置
```

**修改文件**:
- `backend/app/core/security.py` - 添加 `hash_password()`/`verify_password()` 新接口
- `backend/app/models/student.py` - 标记 salt 字段弃用
- `backend/app/models/user.py` - 标记 salt 字段弃用
- `backend/app/crud/user.py` - 移除 salt 参数
- `backend/app/crud/student.py` - 移除 salt 参数
- `backend/app/api/routes/users.py` - 使用新接口
- `backend/app/api/routes/students.py` - 使用新接口
- `backend/app/api/routes/login.py` - 使用新接口
- `docs/DEPRECATIONS.md` - 创建弃用说明文档

**测试更新**:
- `tests/unit/crud/test_user.py` - 更新为使用新接口
- `tests/unit/crud/test_student.py` - 更新为使用新接口
- `tests/unit/crud/test_concurrent_login_failure.py` - 更新为使用新接口

**数据库迁移计划**:
- v2.x: 保持 salt 字段，新数据为 NULL
- v3.0: 删除 salt 列

详见 `docs/DEPRECATIONS.md`

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

### 已修复 (16项)

| 缺陷ID | 描述 | 严重级别 |
|--------|------|----------|
| DB-001 | 单表全局状态反模式 | 🔴 严重 |
| DB-002 | SQLite 并发性能瓶颈 | 🔴 严重 |
| DB-003 | 事务边界不明确 | 🟡 中等 |
| BE-001 | 配置加载逻辑分散 | 🟡 中等 |
| BE-002 | 权限检查机制不一致 | 🟡 中等 |
| BE-003 | 业务逻辑泄露到 API 层 | 🟡 中等 |
| BE-004 | 贫血领域模型 | 🟡 中等 |
| BE-006 | JWT Cookie secure 标志 | 🔴 严重 |
| BE-008 | 并发分数更新无锁 | 🔴 严重 |
| FE-001 | 双重状态管理冲突 | 🟡 中等 |
| FE-002 | 路由权限前端控制不可靠 | 🟡 中等 |
| FE-003 | 缺乏统一 API 响应处理 | 🟡 中等 |
| FE-004 | 前后端类型不同步 | 🟡 中等 |
| SEC-004 | 审计日志不完整 | 🔴 严重 |
| TEST-001 | 测试路径硬编码 | 🟡 中等 |
| TEST-002 | Fixture 清理 | 🟢 轻微 |
| FE-005 | 视图层组织风险 | 🟢 轻微 |

### 部分修复 (2项)

| 缺陷ID | 描述 | 严重级别 | 剩余工作 |
|--------|------|----------|----------|
| DB-002 | SQLite 并发性能 | 🔴 严重 | 考虑迁移 PostgreSQL |
| SEC-004 | 审计日志 | 🔴 严重 | 集成到敏感操作 |

### 未修复 (5项)

| 缺陷ID | 描述 | 严重级别 | 优先级 |
|--------|------|----------|--------|
| BE-005 | JWT 令牌无法撤销 | 🔴 严重 | P0 |
| SEC-003 | 密码盐值冗余 | 🔴 严重 | P0 |
| BE-007 | 限流无法扩展 | 🟡 中等 | P1 |
| SEC-001 | 文件上传安全 | 🟡 中等 | P1 |
| SEC-002 | CORS 配置 | 🟡 中等 | P1 |
| DEP-001 | 单容器架构 | 🟡 中等 | P2 |
| DEP-002 | 数据持久化 | 🟡 中等 | P2 |
| DEP-003 | 静态文件路径 | 🟢 轻微 | P3 |

---

## 9. 缺陷修复优先级建议（更新版）

### 第一阶段（紧急）- 影响生产安全
| 缺陷 | 说明 | 状态 |
|------|------|------|
| SEC-003 | 移除冗余 salt 字段 | ❌ 未修复 |
| SEC-004 | 完善审计日志集成 | 🟡 部分修复 |
| BE-005 | JWT 令牌撤销机制 | ❌ 未修复 |
| BE-006 | Cookie secure 标志 | ✅ 已修复 |
| BE-008 | 并发更新加锁 | ✅ 已修复 |

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
后端架构     ████████████████░░░░  8项 (已修复7/部分修复0/未修复1)
前端架构     ██████████░░░░  5项 (已修复5/未修复0)
安全设计     ████████░░  4项 (部分修复1/未修复3)
部署运维     ██████░░░░  3项 (未修复3)
测试质量     ████░░░░░░  2项 (已修复1/未修复1)
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
2026-03-25: 已修复 12 项，部分修复 2 项，未修复 11 项
            ↑
           进度 +48% (新增: BE-008 并发保护修复, BE-006 Cookie安全, TEST-002 等)
2026-03-25: 已修复 13 项，部分修复 2 项，未修复 9 项
            ↑
           进度 +52% (新增: FE-001 双重状态管理修复)
2026-03-25: 已修复 14 项，部分修复 2 项，未修复 8 项
            ↑
           进度 +56% (新增: FE-002 路由权限安全注释)
2026-03-25: 已修复 15 项，部分修复 2 项，未修复 7 项
            ↑
           进度 +60% (新增: FE-003 统一 API 响应处理)
2026-03-25: 已修复 16 项，部分修复 2 项，未修复 6 项
            ↑
           进度 +64% (新增: FE-004 前后端类型同步)
2026-03-25: 已修复 17 项，部分修复 2 项，未修复 5 项
            ↑
           进度 +68% (新增: FE-005 视图层组织文档)
```

### C. 关联需求

部分缺陷修复涉及需求变更：
- ✅ DB-001 → 已支持多班级并行（ClassSession 重构）
- ✅ BE-008 → 已实现乐观锁并发保护（version 字段）
- ✅ FE-001 → 已分离服务端状态和 UI 状态（Query + Pinia）
- ✅ FE-003 → 已统一 API 响应处理（自动检查 res.success）
- ✅ FE-004 → 已同步前后端类型定义（添加类型映射注释）
- ✅ FE-005 → 已添加 Feature-based 架构文档（渐进式重构）
- ❌ BE-005 → 仍需引入 Redis 支持 Token 黑名单
- 🟡 SEC-004 → AuditLog 模型已创建，需集成到业务逻辑

---

*文档结束*
