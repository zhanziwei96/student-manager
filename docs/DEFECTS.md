# ClassHub 班级管理系统 - 缺陷报告

**文档版本**: v1.0  
**编写日期**: 2026-03-24  
**适用系统**: ClassHub 班级管理系统 v3.0 (frontend-v3分支)  
**架构评估范围**: 前端、后端、数据库、部署、安全

---

## 1. 缺陷汇总

| 缺陷类别 | 数量 | 严重级别分布 |
|----------|------|--------------|
| 数据库架构 | 3 | 🔴 严重: 2, 🟡 中等: 1 |
| 后端架构 | 8 | 🔴 严重: 3, 🟡 中等: 4, 🟢 轻微: 1 |
| 前端架构 | 5 | 🟡 中等: 4, 🟢 轻微: 1 |
| 安全设计 | 4 | 🔴 严重: 2, 🟡 中等: 2 |
| 部署运维 | 3 | 🟡 中等: 2, 🟢 轻微: 1 |
| 测试质量 | 2 | 🟡 中等: 1, 🟢 轻微: 1 |

**总计**: 25 项缺陷  
**🔴 严重**: 7 项 | **🟡 中等**: 14 项 | **🟢 轻微**: 4 项

---

## 2. 数据库架构缺陷

### DB-001: 单表全局状态反模式 🔴 严重
**位置**: `backend/app/crud/checkin.py`  
**缺陷描述**: `ClassSession` 使用固定 ID=1 存储全局状态（当前上课班级），同一时间只能有一个班级上课

```python
def get_class_session(session: Session) -> Optional[ClassSession]:
    return session.get(ClassSession, 1)  # 硬编码 ID=1
```

**影响**:
- 无法支持多班级并行上课（如上午1-2节多个班同时上课）
- 状态耦合导致水平扩展不可能
- 多教师同时操作产生竞争条件

**修复建议**: 重构为 `ClassSchedule` 表，关联教师-班级-时间段，支持并发课堂会话

---

### DB-002: SQLite 并发性能瓶颈 🔴 严重
**位置**: `backend/app/core/db.py`  
**缺陷描述**: 使用 `check_same_thread=False` 绕过 SQLite 线程限制，但未解决并发写入性能问题

```python
engine = create_engine(
    f"sqlite:///{settings.get_database_path()}",
    connect_args={"check_same_thread": False},  # 绕过但不解决
    echo=settings.app.debug
)
```

**影响**:
- 班级签到高峰期（50+学生同时签到）可能出现数据库锁定
- 写操作串行执行，性能受限
- 无法横向扩展到多实例

**修复建议**: 评估迁移至 PostgreSQL，或引入连接池 + 读写分离

---

### DB-003: 事务边界不明确 🟡 中等
**位置**: `backend/app/crud/student.py`  
**缺陷描述**: 业务操作和副作用（日志记录）在同一函数中，事务边界模糊

```python
def update_student_score(session, student_id, delta, reason, operator):
    student.score = new_score  # 主业务
    score_log = ScoreLog(...)  # 副作用
    # 两者是否应在同一事务？
```

**影响**:
- 日志记录失败可能导致成绩更新回滚，或反之
- 难以实现仅重试副作用的场景

**修复建议**: 使用领域事件模式，或明确标记事务边界

---

## 3. 后端架构缺陷

### BE-001: 配置加载逻辑分散 🟡 中等
**位置**: `backend/main.py` + `backend/app/core/config.py`  
**缺陷描述**: 环境文件选择逻辑在 `main.py` 和 `config.py` 中重复实现

```python
# main.py
if ENV == 'testing':
    os.environ['ENV_FILE'] = ...
    
# config.py  
def _get_env_file():
    env_files = {...}  # 重复逻辑
```

**影响**:
- 配置来源不一致，难以追踪
- 环境切换可能产生意外行为

**修复建议**: 统一配置入口，使用单一配置加载器

---

### BE-002: 权限检查机制不一致 🟡 中等
**位置**: `backend/app/api/routes/` 各文件  
**缺陷描述**: 装饰器依赖注入与手动调用混用

```python
# students.py - 依赖注入
@router.get("/students")
async def get_students_list(user: dict = Depends(get_current_user))

# checkin.py - 手动调用
@router.post("/class-session/start")
async def begin_class(request: Request):
    await require_login(request)  # 手动调用
```

**影响**:
- 权限策略分散，难以统一维护
- 违反声明式设计原则

**修复建议**: 统一使用 FastAPI 依赖注入机制

---

### BE-003: 业务逻辑泄露到 API 层 🟡 中等
**位置**: `backend/app/api/routes/students.py`  
**缺陷描述**: 复杂的权限过滤逻辑直接写在 API 层

```python
if is_admin:
    students = get_students(session)
else:
    user_obj = get_user(session, int(user_id))
    assigned_classes = user_obj.get_assigned_classes()
    # ... 复杂过滤逻辑
```

**影响**:
- API 层违反"只负责 HTTP 协议转换"原则
- 相同逻辑在多个端点重复

**修复建议**: 移至 Service 层或使用策略模式

---

### BE-004: 贫血领域模型 🟡 中等
**位置**: `backend/app/models/student.py`  
**缺陷描述**: 模型只有数据字段，无业务行为

```python
class Student(StudentBase, table=True):
    __tablename__ = "students"
    # 纯数据，无业务方法
```

**影响**:
- 业务规则散落在 CRUD 函数中
- 难以封装不变量（如分数范围限制）

**修复建议**: 引入领域模型方法（如 `update_score()`, `can_checkin()`）

---

### BE-005: JWT 令牌无法撤销 🔴 严重
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

### BE-006: JWT 安全设置不当 🔴 严重
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

### BE-007: 限流实现无法扩展 🟡 中等
**位置**: `backend/app/core/config.py` (推测)  
**缺陷描述**: 限流配置使用内存存储

**影响**:
- 多实例部署时，每个实例独立计数
- 攻击者可通过轮询不同实例绕过限流

**修复建议**: 使用 Redis 作为限流存储后端

---

### BE-008: 并发分数更新无锁 🔴 严重
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

### FE-001: 双重状态管理冲突 🟡 中等
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

---

### FE-002: 路由权限前端控制不可靠 🟡 中等
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

---

### FE-003: 缺乏统一 API 响应处理 🟡 中等
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

### FE-004: 前后端类型不同步 🟡 中等
**位置**: `frontend-v3/src/types/` vs `backend/app/models/`  
**缺陷描述**: TypeScript 类型手动维护，与 SQLModel 定义可能不一致

**影响**:
- 后端模型变更后，前端类型可能不同步
- 运行时类型错误

**修复建议**: 引入代码生成工具（如 openapi-typescript）从 API 文档生成类型

---

### FE-005: 视图层组织风险 🟢 轻微
**位置**: `frontend-v3/src/views/`  
**缺陷描述**: 49 个 TS/Vue 文件，只有基本的 views/components 分层

**影响**:
- 随功能增加，缺乏 Feature-based 组织会导致模块耦合

**修复建议**: 按功能域组织（如 `features/students/`, `features/checkin/`）

---

## 5. 安全设计缺陷

### SEC-001: 文件上传缺乏安全控制 🟡 中等
**位置**: `backend/app/api/routes/students.py` (推测)  
**缺陷描述**: 上传目录直接挂载，无文件类型白名单和大小限制

**影响**:
- 可能上传恶意文件
- 文件名冲突风险

**修复建议**: 限制文件类型、大小，使用 UUID 重命名，隔离存储

---

### SEC-002: CORS 配置残留开发环境 🟡 中等
**位置**: `backend/app/core/config.py`  
**缺陷描述**: 默认 CORS 来源包含 localhost

```python
cors_origins: List[str] = Field(default=["http://localhost:3000"])
```

**影响**:
- 生产环境可能遗留不安全的跨域配置

**修复建议**: 生产环境强制配置明确域名列表

---

### SEC-003: 密码盐值冗余存储 🔴 严重
**位置**: `backend/app/models/student.py`  
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

### SEC-004: 审计日志不完整 🔴 严重
**位置**: 全局  
**缺陷描述**: 敏感操作（成绩修改、权限变更）缺乏完整审计日志

**影响**:
- 无法追踪操作来源
- 安全事件难以溯源

**修复建议**: 统一审计中间件，记录操作人、时间、IP、变更前后值

---

## 6. 部署运维缺陷

### DEP-001: 单容器多进程架构 🟡 中等
**位置**: `Dockerfile`  
**缺陷描述**: Nginx + FastAPI + SQLite 在同一容器

**影响**:
- 违反容器单一职责原则
- 无法独立扩展前后端
- 一个进程崩溃影响全部

**修复建议**: 分离为前端容器、后端容器、数据库（或共享存储）

---

### DEP-002: 数据持久化依赖宿主机 🟡 中等
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

### DEP-003: 静态文件路径硬编码 🟢 轻微
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

### TEST-001: 测试配置硬编码绝对路径 🟡 中等
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

### TEST-002: Fixture 数据清理依赖 rollback 🟢 轻微
**位置**: `tests/conftest.py`  
**缺陷描述**: 测试数据通过 `session.rollback()` 清理，异常时可能残留

**影响**:
- 测试隔离性依赖数据库事务
- 某些测试可能需要显式清理

**修复建议**: 使用 `scope="function"` 配合清理函数，或内存数据库

---

## 8. 缺陷修复优先级建议

### 第一阶段（紧急）- 影响生产安全
| 缺陷 | 说明 |
|------|------|
| SEC-003 | 移除冗余 salt 字段 |
| SEC-004 | 完善审计日志 |
| BE-005 | JWT 令牌撤销机制 |
| BE-006 | Cookie secure 标志 |

### 第二阶段（重要）- 影响架构稳定
| 缺陷 | 说明 |
|------|------|
| DB-001 | 多班级并行重构 |
| DB-002 | 数据库并发性能 |
| BE-008 | 分数更新加锁 |
| SEC-001 | 文件上传安全 |

### 第三阶段（优化）- 提升代码质量
| 缺陷 | 说明 |
|------|------|
| FE-001 | 统一状态管理 |
| BE-002 | 统一权限检查 |
| TEST-001 | 修复测试路径 |
| 其他中等/轻微缺陷 |

---

## 9. 附录

### A. 缺陷分布图

```
数据库架构   ████████░░  3项 (严重2/中等1)
后端架构     ████████████████░░░░  8项 (严重3/中等4/轻微1)
前端架构     ██████████░░░░  5项 (中等4/轻微1)
安全设计     ████████░░  4项 (严重2/中等2)
部署运维     ██████░░░░  3项 (中等2/轻微1)
测试质量     ████░░░░░░  2项 (中等1/轻微1)
```

### B. 关联需求

部分缺陷修复涉及需求变更：
- DB-001 → REQ-001 (多班级并行)
- BE-005 → 可能需要引入 Redis 支持 Token 黑名单

---

*文档结束*
