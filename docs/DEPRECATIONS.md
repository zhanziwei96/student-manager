# 弃用说明

---

**文档版本**: v1.1  
**最后更新**: 2026-09-11  
**适用版本**: v3.1.0+  
**状态**: ✅ 已同步代码

---

本文档记录系统中已弃用的功能，以及迁移指南。

---

## Phase 6: 裸班级名参数（class_name）移除

**弃用版本**: v3.0.0（Phase 5 起逐步退出）  
**正式移除版本**: v3.1.0（Phase 6）  
**最后更新**: 2026-09-11

### 背景

系统早期以**裸班级名**（如 `1班`）作为业务接口的班级锚点。`classes` 表的唯一约束是 `(name, major, cohort_year)`，裸班名可跨专业/跨届重复——三个专业各有一个 `1班` 是合法状态。

按裸名反查班级 ID 的实现（`class_cache.get_class_id_by_name`，无 `ORDER BY` 取首行）在重名时任取其一，导致：

- **跨专业串班**：给「软件工程1班」的签到/课表/小组操作落到「计算机1班」
- **越权**：教师权限由 `course_offerings.class_scope` 自由文本按逗号 split 后与裸班名比对——填 `1班` 即获得**所有专业** `1班` 的权限；填 `计科1-2班`（UI 占位符的写法）则匹配不到任何班，教师**静默失去全部班级权限**

### 移除内容

| 移除项 | 替代 |
|--------|------|
| 所有接口的 `class_name` 请求参数 | `class_id: int`（行政班 ID） |
| `course-sessions/class/{class_name}` 路径参数 | `course-sessions/class/{class_id}` |
| `students.class_name` 列 | `students.class_id`（FK） |
| `course_offerings.class_scope` 列 | `course_offering_classes(offering_id, class_id)` 关联表 |
| `class_cache.get_class_id_by_name` / `get_class_ids_by_names` | 无（裸名解析已删除；调用方一律持有 `class_id`） |
| `class_cache.get_class_name_by_id` / `get_class_names` | `get_class_display_name_by_id` / `get_class_display_names`（返回完整展示名） |
| `deps.verify_teacher_class_access(user, class_name, session)` | `verify_teacher_class_access(user, class_id, session)` |

### 迁移指南

**客户端（前端/调用方）**

1. 班级下拉/选择器的 value 由班级名改为班级 `id`（`GET /classes` 已返回 `id` 与 `display_name`）。
2. 请求参数 `class_name` → `class_id`；`class_names: []` → `class_ids: []`。
3. 若此前从响应 `class_name` 反查班级 ID：**不要**再用名字匹配，改从响应新增的 `class_id` 字段取值。
4. **响应的 `class_name` 键仍然存在**，但值变为完整展示名（`2026届软件工程1班`）。纯展示代码无需改动；若曾用该值做**逻辑判断或回传**，必须改用 `class_id`。

**教学班面向范围**

- 创建/更新教学班由 `class_scope: "计科1班,计科2班"` 改为 `class_ids: [3, 4]`。
- **教学班不选任何班级 = 面向全部班级**（通配）。这是为兼容历史数据（生产库存在 `class_scope="所有专业"`）保留的过渡语义：迁移时无法按裸名唯一匹配的旧值会留空，从而走通配。
- 管理员应尽快把「全部班级」的教学班补选为真实班级集合，否则该教师对所有班级（含新建班）持续有权限。

**数据库**

- 迁移 `20260911c_add_course_offering_classes` 会重建 `uix_offering`。**执行前必须确认无重复**：
  ```sql
  SELECT course_id, semester_id, teacher_id FROM course_offerings GROUP BY 1,2,3 HAVING count(*) > 1;
  ```
  有返回行则迁移会失败（原约束含 `class_scope` 维度，去掉后可能撞唯一键）。详见 [SEMESTER_DEPLOYMENT.md](./SEMESTER_DEPLOYMENT.md)。

---

## SEC-003: 密码安全升级

**弃用版本**: v2.2.0  
**正式移除版本**: v3.0.0  
**最后更新**: 2026-03-27

### 背景

系统从 SHA256 + salt 升级为 **bcrypt** 算法进行密码哈希：
- bcrypt 自动处理盐值，安全性更高
- 符合 OWASP 密码存储推荐
- 抵御彩虹表攻击和暴力破解

### 弃用接口

| 旧接口 | 状态 | 替代方案 |
|--------|------|----------|
| `verify_password_hash()` | **已弃用** | `verify_password()` |
| `generate_password_hash()` | **已弃用** | `hash_password()` |
| `salt` 字段 | **已移除** | 无需替换，bcrypt 自动处理 |

### 代码迁移示例

#### 旧代码（已弃用）

```python
from app.core.security import generate_password_hash, verify_password_hash

# 生成密码哈希和盐值
password_hash, salt = generate_password_hash("user_password")

# 验证密码（需要传入 salt）
is_valid = verify_password_hash("user_password", stored_hash, user.salt)
```

#### 新代码（推荐）

```python
from app.core.security import hash_password, verify_password

# 生成密码哈希（bcrypt 自动处理盐值）
password_hash = hash_password("user_password")

# 验证密码（无需 salt 参数）
is_valid = verify_password("user_password", stored_hash)
```

### 数据库变更（历史记录，SQLite 时代）

**执行迁移脚本**（旧文档保留，现数据库为 PostgreSQL，alembic 管理迁移）:
```bash
# 历史命令（已不再适用）：
# sqlite3 backend/app/data/class_system.db < migrations/remove_salt_field.sql
```

**变更内容**:
| 表 | 变更 |
|----|------|
| `users` | 移除 `salt` 列 |
| `students` | 移除 `salt` 列 |

### 对现有用户的影响

- **bcrypt 密码用户**: 无影响，正常登录
- **旧版 SHA256 密码用户**: 需要重置密码（系统不再支持 SHA256 验证）

### 安全建议

1. 生产环境部署后，建议所有用户重置密码
2. 启用密码强度验证
3. 定期审计密码哈希算法

---

## JWT 时区处理更新

**更新版本**: v2.3.0  
**最后更新**: 2026-03-27

### 变更说明

JWT Token 的过期时间计算从 `datetime.utcnow()` 改为 `datetime.now(ZoneInfo("Asia/Shanghai"))`：

| 项目 | 旧实现 | 新实现 |
|------|--------|--------|
| 时区 | UTC | Asia/Shanghai |
| 函数 | `datetime.utcnow()` | `datetime.now(ZoneInfo("Asia/Shanghai"))` |
| Token 过期 | UTC 时间 | 东八区时间 |

### 代码示例

#### 新实现

```python
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 使用统一时区
timezone = ZoneInfo("Asia/Shanghai")
now = datetime.now(timezone)
expire = now + timedelta(hours=24)

payload = {
    "sub": str(user.id),
    "exp": expire,
    "iat": now,
}
```

### 影响

- 现有 Token 在过期前仍然有效
- 新颁发的 Token 使用统一时区
- 避免因服务器时区配置不一致导致的 Token 问题

---

## 限流状态码更新

**更新版本**: v2.3.0  
**最后更新**: 2026-03-27  
**问题ID**: RATE-001

### 变更说明

限流触发时的状态码从 **503 Service Unavailable** 改为 **429 Too Many Requests**：

| 场景 | 旧状态码 | 新状态码 |
|------|----------|----------|
| 登录限流 | 503 | 429 |
| API 限流 | 503 | 429 |

### 代码示例

```python
from fastapi import HTTPException

# 正确 - 限流响应
raise HTTPException(
    status_code=429,
    detail="请求过于频繁，请稍后再试"
)

# 错误 - 不要再使用
# raise HTTPException(status_code=503, detail="服务不可用")
```

### 客户端适配

前端需要处理 429 状态码：

```typescript
// 处理限流响应
if (response.status === 429) {
  toast.error('操作过于频繁，请稍后再试');
  return;
}
```

---

## salt 字段弃用（历史记录）

**弃用版本**: v2.2.0  
**计划移除版本**: v3.0.0  
**状态**: **已移除** (2026-03-27)

### 背景

bcrypt 算法的设计理念是**自动处理盐值**：
- 每次哈希时自动生成随机盐值
- 盐值直接内嵌在哈希字符串中（格式: `$2b$12$<salt><hash>`）
- 验证时从哈希字符串中提取盐值

因此，单独存储 `salt` 字段是冗余的。

### 影响范围

| 表 | 字段 | 状态 |
|----|------|------|
| `users` | `salt` | **已移除** |
| `students` | `salt` | **已移除** |

### 迁移脚本

```sql
-- 删除 users 表的 salt 列
ALTER TABLE users DROP COLUMN salt;

-- 删除 students 表的 salt 列
ALTER TABLE students DROP COLUMN salt;
```

---

## 弃用功能时间线

```
v2.2.0 (2026-03-25)
├── 弃用: verify_password_hash()
├── 弃用: generate_password_hash()
├── 弃用: salt 字段
└── 引入: bcrypt 算法

v2.3.0 (2026-03-26)
├── 修复: 限流状态码 503→429
├── 更新: JWT 时区统一为 Asia/Shanghai
└── 移除: salt 字段（执行迁移脚本）

v3.0.0 (计划)
├── 正式移除旧接口（已提前移除）
└── 清理向后兼容代码
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [API 变更日志](./API_CHANGELOG.md) | API 版本变更记录 |
| [后端架构](../backend/README.md) | 后端架构与安全实现 |
| [CLAUDE.md](../CLAUDE.md) | 开发规范与约束 |

---

**文档版本**: 2026-03-27  
**最后更新**: SEC-003 密码安全升级、RATE-001 限流状态码修复、JWT 时区统一
