# 数据库迁移说明

## 迁移状态

✅ **迁移已完成** - 数据已从旧系统迁移到新架构

## 迁移详情

### 迁移时间
2026-03-22

### 迁移内容

| 表 | 主要变更 |
|---|---------|
| `users` | `is_admin` → `role` 字符串，新增安全字段（login_fail_count, locked_until 等） |
| `students` | `score` INTEGER → REAL，支持小数分数 |
| `checkin_records` | 新增 `student_name`、`class_name`、`checkin_type` 字段 |
| `score_logs` | 完全重构，记录 old_score/new_score/delta/reason/operator |
| `class_session` | 新增上课状态表 |

### 数据迁移统计

- 学生：462 名
- 用户：2 名（admin, teacher）
- 分数日志：586 条
- 签到记录：3 条

## 当前数据库

```bash
# 数据库路径
/home/yufeng/student-manager/backend/data/class_system.db

# 连接数据库
sqlite3 /home/yufeng/student-manager/backend/data/class_system.db

# 查看表结构
.tables
.schema users
.schema students
```

## 备份恢复

如需从备份恢复：

```bash
# 停止服务
pkill -f "python main.py"

# 恢复备份
mv backend/data/class_system.db backend/data/class_system.db.failed
mv backend/data/class_system.db.backup.YYYYMMDD backend/data/class_system.db

# 重启
python backend/main.py
```

## 历史迁移脚本

旧迁移脚本位于 `migrations/` 目录，仅用于参考：
- `migrate_v1_to_v2.sql` - v1 到 v2 的表结构变更

---

**注意**: 当前系统使用 SQLModel 自动管理表结构，无需手动执行迁移脚本。
