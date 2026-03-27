# 后端代码审查报告

> 审查时间：2026-03-26  
> **复查时间：2026-03-27**
> 审查者：后端设计 Agent  
> 技术栈：FastAPI + SQLModel + SQLite

---

## 📋 复查摘要（2026-03-27）

### 复查评分

| 模块 | 上次评分 | **当前评分** | 变化 |
|------|----------|--------------|------|
| **架构设计** | 8.0/10 | **8.5/10** | ⬆️ +0.5 |
| **API设计** | 8.0/10 | **8.5/10** | ⬆️ +0.5 |
| **安全性** | 7.5/10 | **8.0/10** | ⬆️ +0.5 |
| **性能** | 8.0/10 | **8.0/10** | ➡️ 持平 |
| **代码质量** | 8.0/10 | **8.5/10** | ⬆️ +0.5 |
| **综合评分** | **7.2/10** | **8.3/10** | ⬆️ **+1.1** |

### 修复状态

| 问题 | 状态 | 说明 |
|------|------|------|
| **SEC-003: verify_password_hash** | ✅ 已修复 | 使用`verify_password()`替代，移除salt字段 |
| **503限流状态码** | ✅ 已修复 | 改为429 (TOO_MANY_REQUESTS) |
| **JWT时区问题** | ✅ 已修复 | 统一使用Asia/Shanghai |
| **删除用户类型不一致** | ✅ 已修复 | 统一使用int比较 |
| **签到接口认证** | ✅ 已修复 | 添加认证要求 |
| **system/stats接口认证** | ✅ 已修复 | 添加认证要求 |

### 仍存在的问题
- ❌ **修改密码后旧会话未失效**（P0 - 中高危）
- ⚠️ **乐观锁实现不完整**（P1 - 无唯一约束）
- ⚠️ **API层直接操作Session**（P1 - users.py:112-114）
- ⚠️ **审计日志同步写入**（P1 - 性能瓶颈）

---

> 以下是原始审查报告（2026-03-26）

---

## 总体评分：72/100

**代码质量评级**：B

---

## 🔴 严重问题（必须立即修复）

| 序号 | 文件 | 行号 | 问题描述 | 风险 | 修复代码 |
|------|------|------|----------|------|----------|
| 1 | login.py | L96, L140 | 使用已弃用的 `verify_password_hash` 函数并传递 salt 参数，该函数在 SEC-003 中已被标记为弃用，且 bcrypt 不需要 salt | 登录失败/安全兼容性问题 | ```python\nfrom app.core.security import verify_password\n# 移除 salt 参数\nif not verify_password(password, student.password_hash):\n    ...\n``` |
| 2 | login.py | L82 | 限流触发返回 HTTP 503 (SERVICE_UNAVAILABLE)，这是服务不可用状态码，应返回 429 (TOO_MANY_REQUESTS) | HTTP语义错误/客户端处理混乱 | ```python\nfrom app.core.config import HttpStatus\n# 添加 TOO_MANY_REQUESTS = 429\nraise HTTPException(\n    status_code=HttpStatus.TOO_MANY_REQUESTS,\n    detail='请求过于频繁，请稍后再试'\n)\n``` |
| 3 | users.py | L162 | 删除用户时 `current_user_id` 是 str 类型而 `user_id` 是 int，类型不一致导致比较结果不可预期 | 管理员可能意外删除自己账户 | ```python\n# 统一使用 int 比较\nif int(user_id) == int(current_user_id):\n    raise HTTPException(...)\n``` |
| 4 | student.py | L226-232 | 乐观锁实现有缺陷：`IntegrityError` 无法捕获乐观锁冲突，因为版本号检查需要显式的 WHERE 条件 | 并发更新时数据丢失 | ```python\nfrom sqlalchemy import and_\n# 使用 UPDATE ... WHERE version = :version 模式\nresult = session.execute(\n    update(Student)\n    .where(and_(Student.student_id == student_id, Student.version == student.version))\n    .values(score=new_score, version=Student.version + 1)\n)\nif result.rowcount == 0:\n    raise HTTPException(status_code=409, detail="并发修改冲突")\n``` |
| 5 | jwt.py | L22, L76 | 使用 `datetime.utcnow()` 在 Python 3.12+ 已弃用，且时区处理不当可能导致 JWT 过期判断错误 | 认证绕过/提前过期 | ```python\nfrom datetime import datetime, timezone\nexpire = datetime.now(timezone.utc) + expires_delta\n# 检查时\nif datetime.now(timezone.utc).timestamp() > exp:\n    raise HTTPException(...)\n``` |

---

## 🟡 中等问题

| 序号 | 文件 | 问题 | 影响 | 建议 |
|------|------|------|------|------|
| 1 | checkin.py L114-150 | 签到接口没有认证要求，任何人都可以调用 | 恶意签到/数据污染 | 添加 `user: dict = Depends(get_current_user)` 依赖，确保只有学生或教师能签到 |
| 2 | system.py L27-43 | `/stats` 接口没有认证要求，但代码注释说"需要登录" | 信息泄露 | 添加 `user: dict = Depends(get_current_user)` 依赖 |
| 3 | student.py L54-70, L91-103 | 权限检查在 CRUD 层，但返回的是 `(None, error)` 元组，API 层需要额外处理 | 代码重复/维护困难 | 统一在 API 层做权限检查，CRUD 层只负责数据操作 |
| 4 | checkin.py L202-209 | 计算签到率时先查询所有学生再内存计算，没有分页 | 大数据集时内存溢出 | 使用 SQL `COUNT()` 聚合查询，避免加载所有学生对象 |
| 5 | audit.py L63-71 | 清理旧日志使用逐条删除，效率低下 | 性能问题/数据库锁定 | 使用 `DELETE FROM audit_logs WHERE created_at < ?` 批量删除 |
| 6 | user.py L117-141 | `record_login_failure` 使用重试循环处理乐观锁，但没有指数退避 | 高并发时数据库压力 | 添加指数退避延迟：`time.sleep(0.1 * (2 ** attempt))` |
| 7 | schedules.py L84-230 | 导入课表在事务中逐条处理，失败时部分数据已提交 | 数据不一致 | 使用 `@router.post(...)` 配合异常处理，或使用 `session.begin()` 确保原子性 |

---

## 🟢 轻微问题

| 序号 | 文件 | 问题 | 建议 |
|------|------|------|------|
| 1 | login.py L227 | `hash_password` 导入在函数内，应放在文件顶部 | 移到文件顶部 import |
| 2 | users.py L107 | `json.dumps` 导入在函数内 | 移到文件顶部 |
| 3 | schedules.py L14-18 | 从 upload.py 导入私有函数 `_validate_filename` 等 | 将这些函数改为公共 API 或创建公共接口 |
| 4 | checkin.py L129, L162 | 函数内导入 `get_class_session_by_class_name` | 移到文件顶部 |
| 5 | students.py L43, L182 | 函数内导入权限检查函数 | 统一在顶部导入 |
| 6 | login.py L86-123 | 学生登录逻辑和管理员登录逻辑重复 | 提取为通用认证函数 |
| 7 | config.py L244-254 | `HttpStatus` 缺少常用状态码如 429 | 添加 `TOO_MANY_REQUESTS = 429` |

---

## 代码异味汇总

| 异味类型 | 出现位置 | 改进建议 |
|----------|----------|----------|
| 重复代码 | login.py:86-123, login.py:125-179 | 提取通用认证逻辑到 `authenticate_user()` 函数 |
| 重复代码 | students.py:60-68, student.py:57-69 | 去重逻辑在 `get_students_by_permission` 和 API 层重复 |
| 过长函数 | schedules.py:84-230 (146行) | 拆分导入逻辑：验证、解析、保存 |
| 函数内导入 | 多个文件多处 | 统一移到顶部，提高可读性 |
| 混合关注点 | student.py:11-103 (权限+CRUD) | 权限检查应在 API 层，CRUD 只负责数据 |
| 魔法字符串 | schedules.py:38, users.py:49 | 使用 `UserRoleConst.TEACHER` 常量 |
| 类型不一致 | users.py 多处 user_id | 统一使用 int 类型 |

---

## 安全审计

| 检查项 | 状态 | 说明 |
|--------|------|------|
| SQL注入防护 | ✅ | 使用 SQLModel/SQLAlchemy ORM，参数化查询 |
| XSS防护 | ⚠️ | 依赖前端处理，后端返回的数据没有转义 |
| 认证安全 | ⚠️ | JWT 实现基本正确，但 `utcnow()` 已弃用 |
| 授权检查 | ⚠️ | `/checkin` 和 `/stats` 缺少认证 |
| 敏感数据加密 | ✅ | 密码使用 bcrypt 哈希 (12轮) |
| 文件上传安全 | ✅ | 有扩展名白名单、MIME检查、大小限制 |
| 密码长度限制 | ⚠️ | bcrypt 截断 72 字节，但前端/后端没有明确提示 |
| 敏感信息泄露 | ⚠️ | `/dashboard` 接口返回脱敏数据，但 `student_id_mask` 可能可逆 |
| Cookie安全 | ⚠️ | `secure` 标志默认 False，生产环境需手动开启 |

---

## 性能瓶颈分析

| 位置 | 问题 | 当前复杂度 | 优化后 | 预期提升 |
|------|------|------------|--------|----------|
| system.py:32-34 | 全表加载学生/签到数据 | O(n) 内存 | O(1) COUNT 查询 | 内存占用降低 90%+ |
| checkin.py:202-209 | 加载所有学生计算签到率 | O(n) 内存+CPU | SQL COUNT + JOIN | 查询时间降低 80% |
| students.py:45-70 | 教师查询加载所有班级学生 | O(n*m) | 使用 SQL IN 查询 | 减少 N+1 查询 |
| student.py:57-69 | 去重逻辑在 Python 中 | O(n²) | 使用 SQL DISTINCT | CPU 降低 50% |
| audit.py:66-71 | 逐条删除旧日志 | O(n) 查询 + n次DELETE | 批量 DELETE | 删除速度提升 10x |
| students.py:262-276 | 分数日志可能无限制增长 | O(n) 查询 | 添加分页/时间过滤 | 响应时间稳定 |

---

## 特别关注项分析

### 1. 并发分数更新竞态条件

**位置**: `student.py:151-246`

当前实现声称使用乐观锁，但实现不完整：
- 只递增 `version` 字段，但没有在 UPDATE 的 WHERE 子句中检查版本
- `IntegrityError` 无法捕获乐观锁冲突（需要唯一约束冲突才会抛出）
- **风险**: 高并发下多个教师同时修改同一学生分数时可能丢失更新

**建议修复**:
```python
from sqlalchemy import update, and_
from sqlalchemy.orm import selectinload

# 使用原生 UPDATE with WHERE
result = session.execute(
    update(Student)
    .where(and_(
        Student.student_id == student_id,
        Student.version == student.version
    ))
    .values(
        score=new_score,
        version=Student.version + 1
    )
)

if result.rowcount == 0:
    raise HTTPException(status_code=409, detail="并发修改冲突")
```

### 2. JWT Token 安全隐患

**位置**: `jwt.py:13-25`

问题：
- 密钥从配置文件读取，默认值为 `"dev-secret-key-change-in-production"`
- 如果部署时未修改，攻击者可伪造 Token
- Token 有效期 24 小时较长，没有 Refresh Token 机制

### 3. 数据库事务使用

**位置**: 多处

问题：
- 部分操作在 `try/except` 中没有正确回滚
- `session.commit()` 后没有处理可能的异常
- `get_session()` 依赖注入没有异常处理包装器

### 4. 异常处理

**位置**: 多处

问题：
- 很多数据库操作没有捕获 `SQLAlchemyError`
- 原始异常信息直接返回给客户端（可能泄露内部实现）
- 缺少全局异常处理器统一处理数据库错误

---

## 重构建议

### 1. 权限检查层统一

```python
# 建议结构
# api/deps.py
def require_teacher(user: dict = Depends(get_current_user)):
    if user.get('role') != UserRole.TEACHER:
        raise HTTPException(403, "需要教师权限")
    return user

# routes/students.py
@router.get("/students")
def list_students(user: dict = Depends(require_teacher)):
    # 无需再检查权限
    return crud.get_students()
```

### 2. 统一响应格式

```python
# core/response.py
class APIResponse(BaseModel):
    success: bool
    data: Any = None
    message: str = ""
    code: int = 200

def success_response(data: Any, message: str = ""):
    return APIResponse(success=True, data=data, message=message)

def error_response(message: str, code: int = 400):
    return APIResponse(success=False, message=message, code=code)
```

### 3. 全局异常处理

```python
# core/exceptions.py
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "数据库错误"}
    )
```

---

**审查完成时间**: 2026-03-26  
**审查者**: 后端代码审查 Agent
