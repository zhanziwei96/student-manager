# 弃用说明

本文档记录系统中已弃用的功能，以及迁移指南。

---

## SEC-003: salt 字段弃用

**弃用版本**: v2.2.0  
**计划移除版本**: v3.0.0

### 背景

系统使用 bcrypt 算法进行密码哈希。bcrypt 算法的设计理念是**自动处理盐值**：
- 每次哈希时自动生成随机盐值
- 盐值直接内嵌在哈希字符串中（格式: `$2b$12$<salt><hash>`）
- 验证时从哈希字符串中提取盐值

因此，单独存储 `salt` 字段是冗余的。

### 影响范围

| 表 | 字段 | 状态 |
|----|------|------|
| `users` | `salt` | 已弃用，新数据为 NULL |
| `students` | `salt` | 已弃用，新数据为 NULL |

### 代码变更

#### 新的推荐接口

```python
from app.core.security import hash_password, verify_password

# 生成密码哈希（bcrypt 自动处理盐值）
password_hash = hash_password("user_password")

# 验证密码
is_valid = verify_password("user_password", stored_hash)
```

#### 向后兼容接口（仍然可用）

```python
from app.core.security import generate_password_hash, verify_password_hash

# 仍然可用，但 salt 始终返回空字符串
password_hash, _ = generate_password_hash("user_password")

# 仍然可用，但 salt 参数被忽略
is_valid = verify_password_hash("user_password", stored_hash, user.salt)
```

### 数据库迁移计划

在 v3.0.0 版本中，将执行以下迁移：

```sql
-- 删除 users 表的 salt 列
ALTER TABLE users DROP COLUMN salt;

-- 删除 students 表的 salt 列
ALTER TABLE students DROP COLUMN salt;
```

### 对现有用户的影响

- **bcrypt 密码用户**: 无影响，正常登录
- **旧版 SHA256 密码用户**: 需要重置密码（系统不再支持 SHA256 验证）

---

## 其他弃用

暂无其他弃用功能。

---

**文档版本**: 2026-03-25  
**最后更新**: SEC-003 密码盐值冗余存储修复
