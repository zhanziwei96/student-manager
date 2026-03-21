# 数据库迁移速查

## 旧数据库 → 新结构

```bash
# 1. 备份
cp backend/data/class_system.db \
   backend/data/class_system.db.backup.$(date +%Y%m%d)

# 2. 执行迁移
sqlite3 backend/data/class_system.db < migrations/migrate_v1_to_v2.sql

# 3. 验证
sqlite3 backend/data/class_system.db ".schema users"
```

## 结构差异

| 表 | 主要变更 |
|---|---------|
| `users` | `is_admin` → `role`，新增安全字段 |
| `students` | `score` INTEGER → REAL |
| `checkin_records` | `record_id` → `id`，新增 student_name/class_name |
| `score_logs` | 完全重构，记录 old_score/new_score/delta |

## 迁移后处理

```sql
-- 1. 分配教师班级
UPDATE users SET assigned_class = '软件1班' WHERE username = 'xxx';

-- 2. 检查数据
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM students;
SELECT username, role FROM users WHERE role='admin';
```

## 回滚

```bash
# 停止服务
pkill -f "python main.py"

# 恢复备份
mv backend/data/class_system.db backend/data/class_system.db.failed
mv backend/data/class_system.db.backup.YYYYMMDD backend/data/class_system.db

# 重启
python backend/main.py
```

---

详细说明见 [migrations/README.md](../migrations/README.md)
