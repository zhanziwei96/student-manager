# 弃用说明

---

**文档版本**: v1.0  
**最后更新**: 2026-04-03  
**适用版本**: v3.0.0+  
**状态**: ✅ 已同步代码

---

本文档记录系统中已弃用的功能，以及迁移指南。

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

### 数据库变更

**执行迁移脚本**:
```bash
sqlite3 backend/data/class_system.db < migrations/remove_salt_field.sql
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

**文档版本**: 2026-03-27  
**最后更新**: SEC-003 密码安全升级、RATE-001 限流状态码修复、JWT 时区统一
