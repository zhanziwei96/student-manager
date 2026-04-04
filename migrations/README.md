# 数据库迁移指南

## 概述

本项目从旧的数据库结构（`class_system.db`）迁移到新的 DDD 架构数据库结构。

**最后更新**: 2026-03-27

---

## 迁移脚本

### 1. migrate_v1_to_v2.sql - 完整结构迁移

**用途**: 将旧数据库结构完整迁移到新结构

**主要变更**:

| 表 | 变更内容 |
|---|---------|
| `users` | `is_admin` → `role`，添加安全字段（assigned_class, is_active, login_fail_count, locked_until, last_login_ip） |
| `checkin_records` | `record_id` → `id`，添加 student_name, class_name |
| `score_logs` | 完全重构，从简单记录改为详细记录（old_score, new_score, delta, operator） |
| `students` | `score` 从 INTEGER 改为 REAL |

**使用方法**:

```bash
# 备份旧数据库
cp backend/data/class_system.db backend/data/class_system.db.backup.$(date +%Y%m%d)

# 执行迁移
sqlite3 backend/data/class_system.db < migrations/migrate_v1_to_v2.sql

# 验证
sqlite3 backend/data/class_system.db ".schema"
```

---

### 2. add_security_tables.sql - 增量安全表

**用途**: 在现有数据库上添加安全相关表（审计日志、安全告警）

**使用场景**: 数据库结构已是最新，只需要添加安全功能表

```bash
sqlite3 backend/data/student_manage.db < migrations/add_security_tables.sql
```

---

### 3. add_version_optimistic_lock.sql - 乐观锁版本字段（BE-008 修复）

**用途**: 为学生表和用户信息表添加乐观锁版本字段，防止并发更新导致的数据丢失

**主要变更**:

| 表 | 变更内容 |
|---|---------|
| `students` | 添加 `version` 字段（INTEGER DEFAULT 1）用于乐观锁 |
| `users` | 添加 `version` 字段（INTEGER DEFAULT 1）用于乐观锁 |

**使用场景**: 修复 BE-008 并发分数更新无锁问题，确保并发操作时数据一致性

```bash
# 执行迁移
sqlite3 backend/data/class_system.db < migrations/add_version_optimistic_lock.sql

# 验证迁移结果
sqlite3 backend/data/class_system.db "SELECT COUNT(*) FROM students WHERE version IS NOT NULL;"
sqlite3 backend/data/class_system.db "SELECT COUNT(*) FROM users WHERE version IS NOT NULL;"
```

**注意事项**:
- 迁移前必须备份数据库
- 现有数据会自动设置 version=1
- 此迁移与代码版本配套，迁移后需更新代码到包含乐观锁的版本

---

### 4. remove_salt_field.sql - 移除 salt 字段（SEC-003 修复）

**用途**: 移除 `users` 和 `students` 表的 `salt` 字段

**背景**: 
- 系统已升级为 bcrypt 算法进行密码哈希
- bcrypt 自动处理盐值，单独存储 `salt` 字段是冗余的
- 参见 [SEC-003 安全升级](../docs/DEPRECATIONS.md)

**主要变更**:

| 表 | 变更内容 |
|---|---------|
| `users` | 移除 `salt` 列 |
| `students` | 移除 `salt` 列 |

**使用场景**: 完成 SEC-003 密码安全升级后，清理冗余的 salt 字段

```bash
# 执行迁移
sqlite3 backend/data/class_system.db < migrations/remove_salt_field.sql

# 验证迁移结果 - 检查 users 表结构
sqlite3 backend/data/class_system.db ".schema users"

# 验证迁移结果 - 检查 students 表结构
sqlite3 backend/data/class_system.db ".schema students"

# 确认 salt 字段已移除（查询应报错或显示无 salt 列）
sqlite3 backend/data/class_system.db "SELECT salt FROM users LIMIT 1;" 2>&1 || echo "salt 字段已移除"
```

**执行前检查**:

```bash
# 1. 确认当前密码哈希算法为 bcrypt
sqlite3 backend/data/class_system.db "SELECT password_hash FROM users WHERE role='admin' LIMIT 1;"
# 应返回 $2b$12$... 格式的 bcrypt 哈希

# 2. 备份数据库
cp backend/data/class_system.db backend/data/class_system.db.backup.pre-salt-removal.$(date +%Y%m%d)

# 3. 确认所有新用户都使用 bcrypt
sqlite3 backend/data/class_system.db "SELECT COUNT(*) FROM users WHERE password_hash NOT LIKE '\$2b\$%';"
# 应返回 0（如果返回非零，表示还有旧版 SHA256 密码需要处理）
```

**注意事项**:
- ⚠️ **此迁移不可逆**，执行前务必备份数据库
- 确保所有密码已升级为 bcrypt 格式
- 旧版 SHA256 密码用户将无法登录，需要重置密码
- 执行迁移后，代码中的 `salt` 相关逻辑可以安全移除

---

### 5. add_student_account.sql - 学生账号支持

**用途**: 为学生添加账号登录功能

**主要变更**:

| 表 | 变更内容 |
|---|---------|
| `students` | 添加 `password_hash` 字段 |
| `students` | 添加 `is_active` 字段 |
| `students` | 添加 `last_login` 字段 |

**使用场景**: 学生需要使用学号登录系统

```bash
sqlite3 backend/data/class_system.db < migrations/add_student_account.sql
```

---

### 6. add_course_schedule.sql - 课程表支持

**用途**: 添加课程表功能

**主要变更**:

| 表 | 说明 |
|---|------|
| `course_schedules` | 新课程表表，存储课程安排 |

**使用场景**: 需要课程表功能

```bash
sqlite3 backend/data/class_system.db < migrations/add_course_schedule.sql
```

---

### 7. add_class_session_active_index.sql - 活跃课堂索引优化

**用途**: 为 `class_session` 表的 `active` 字段添加索引，优化"正在上课"查询性能

**背景**:
- Admin 仪表盘需要实时显示活跃课堂列表
- 缺少索引导致每次查询都进行全表扫描
- 数据量增加后性能显著下降

**主要变更**:

| 表 | 变更内容 |
|---|---------|
| `class_session` | 添加 `idx_session_active` 索引 (active 字段) |

**使用场景**: Admin 仪表盘"正在上课"模块加载缓慢

```bash
# 执行迁移
sqlite3 backend/data/class_system.db < migrations/add_class_session_active_index.sql

# 验证索引创建
sqlite3 backend/data/class_system.db ".schema class_session"
# 应包含: CREATE INDEX idx_session_active ON class_session(active)
```

---

## 迁移前检查清单

- [ ] 已备份数据库
- [ ] 确认没有正在进行的业务操作
- [ ] 检查数据库文件路径正确
- [ ] 验证 SQLite3 版本 >= 3.25（支持 ALTER TABLE RENAME COLUMN）

---

## 数据兼容性说明

### 完全兼容 ✅
- students 表：数据可完整迁移
- users 表：基础信息可完整迁移，新增字段使用默认值

### 部分兼容 ⚠️
- checkin_records：学生姓名/班级尝试从 students 表补全，可能为 NULL
- score_logs：旧数据缺少 old_score/new_score/operator 字段，迁移后设为 NULL

### 不兼容 ❌
- class_session 表：新代码未使用，可选择保留或删除

---

## 完整迁移流程（新环境部署）

如果是新环境部署，按顺序执行以下迁移：

```bash
# 1. 基础结构迁移（如果是从旧版本升级）
# sqlite3 backend/data/class_system.db < migrations/migrate_v1_to_v2.sql

# 2. 添加安全表
sqlite3 backend/data/class_system.db < migrations/add_security_tables.sql

# 3. 添加学生账号支持
sqlite3 backend/data/class_system.db < migrations/add_student_account.sql

# 4. 添加乐观锁版本字段
sqlite3 backend/data/class_system.db < migrations/add_version_optimistic_lock.sql

# 5. 添加课程表支持（可选）
# sqlite3 backend/data/class_system.db < migrations/add_course_schedule.sql

# 6. 移除 salt 字段（完成 SEC-003 升级后）
# sqlite3 backend/data/class_system.db < migrations/remove_salt_field.sql

# 验证迁移结果
sqlite3 backend/data/class_system.db ".schema"
sqlite3 backend/data/class_system.db ".tables"
```

---

## 迁移后需要手动处理的事项

1. **分配教师班级**: users.assigned_class 需要管理员手动分配
   ```sql
   UPDATE users SET assigned_class = '软件1班' WHERE username = 'xxx';
   ```

2. **补全分数日志**: score_logs 中的 old_score/new_score 字段为 NULL，如需补全需人工处理

3. **配置新功能**: 启用账号锁定、登录失败次数限制等新功能

4. **处理旧版密码**: 如果有 SHA256 密码用户，需要联系重置密码

---

## 验证迁移成功

```bash
# 1. 检查表结构
sqlite3 backend/data/class_system.db ".schema users"

# 2. 检查数据量
sqlite3 backend/data/class_system.db "SELECT COUNT(*) FROM users;"
sqlite3 backend/data/class_system.db "SELECT COUNT(*) FROM students;"

# 3. 验证角色转换
sqlite3 backend/data/class_system.db "SELECT username, role FROM users WHERE role='admin';"

# 4. 验证乐观锁字段
sqlite3 backend/data/class_system.db "SELECT username, version FROM users LIMIT 5;"

# 5. 启动后端测试
ENV=testing python backend/main.py
```

---

## 回滚方案

如果迁移失败，使用备份恢复：

```bash
# 停止后端服务
pkill -f "python main.py"

# 恢复备份
mv backend/data/class_system.db backend/data/class_system.db.failed
mv backend/data/class_system.db.backup.YYYYMMDD backend/data/class_system.db

# 重新启动后端
python backend/main.py
```

---

## 注意事项

1. 迁移脚本使用事务，失败会自动回滚
2. 外键约束在迁移期间被禁用，迁移后重新启用
3. 建议在生产环境先在测试数据库上验证迁移脚本
4. **remove_salt_field.sql 是不可逆操作**，执行前务必备份

---

## 迁移脚本索引

| 脚本 | 用途 | 是否必需 | 执行顺序 |
|------|------|----------|----------|
| migrate_v1_to_v2.sql | 旧版本升级 | 升级时必需 | 1 |
| add_security_tables.sql | 安全功能 | 推荐 | 2 |
| add_student_account.sql | 学生登录 | 推荐 | 3 |
| add_version_optimistic_lock.sql | 乐观锁 | 推荐 | 4 |
| add_course_schedule.sql | 课程表 | 可选 | 5 |
| add_class_session_active_index.sql | 活跃课堂索引 | 性能优化 | 6 |
| remove_salt_field.sql | 清理 salt | 可选 | 最后 |

---

**文档版本**: 2026-04-04  
**最后更新**: 新增 add_class_session_active_index.sql 活跃课堂索引优化
