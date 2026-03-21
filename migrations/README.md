# 数据库迁移指南

## 概述

本项目从旧的数据库结构（`class_system.db`）迁移到新的 DDD 架构数据库结构。

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

### 2. add_security_tables.sql - 增量安全表

**用途**: 在现有数据库上添加安全相关表（审计日志、安全告警）

**使用场景**: 数据库结构已是最新，只需要添加安全功能表

```bash
sqlite3 backend/data/student_manage.db < migrations/add_security_tables.sql
```

## 迁移前检查清单

- [ ] 已备份数据库
- [ ] 确认没有正在进行的业务操作
- [ ] 检查数据库文件路径正确
- [ ] 验证 SQLite3 版本 >= 3.25（支持 ALTER TABLE RENAME COLUMN）

## 数据兼容性说明

### 完全兼容 ✅
- students 表：数据可完整迁移
- users 表：基础信息可完整迁移，新增字段使用默认值

### 部分兼容 ⚠️
- checkin_records：学生姓名/班级尝试从 students 表补全，可能为 NULL
- score_logs：旧数据缺少 old_score/new_score/operator 字段，迁移后设为 NULL

### 不兼容 ❌
- class_session 表：新代码未使用，可选择保留或删除

## 迁移后需要手动处理的事项

1. **分配教师班级**: users.assigned_class 需要管理员手动分配
   ```sql
   UPDATE users SET assigned_class = '软件1班' WHERE username = 'xxx';
   ```

2. **补全分数日志**: score_logs 中的 old_score/new_score 字段为 NULL，如需补全需人工处理

3. **配置新功能**: 启用账号锁定、登录失败次数限制等新功能

## 验证迁移成功

```bash
# 1. 检查表结构
sqlite3 backend/data/class_system.db ".schema users"

# 2. 检查数据量
sqlite3 backend/data/class_system.db "SELECT COUNT(*) FROM users;"
sqlite3 backend/data/class_system.db "SELECT COUNT(*) FROM students;"

# 3. 验证角色转换
sqlite3 backend/data/class_system.db "SELECT username, role FROM users WHERE role='admin';"

# 4. 启动后端测试
ENV=testing python backend/main.py
```

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

## 注意事项

1. 迁移脚本使用事务，失败会自动回滚
2. 外键约束在迁移期间被禁用，迁移后重新启用
3. 建议在生产环境先在测试数据库上验证迁移脚本
