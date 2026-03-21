-- ============================================
-- 班级管理系统数据库迁移脚本
-- 从旧结构(class_system.db)迁移到新结构
-- ============================================

-- 开启外键约束检查
PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- ============================================
-- 1. users 表迁移（is_admin -> role，添加安全字段）
-- ============================================

-- 创建新 users 表
CREATE TABLE users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'teacher',
    assigned_class TEXT,
    is_active INTEGER DEFAULT 1,
    login_fail_count INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    last_login_ip TEXT,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 迁移数据：is_admin = 1 -> role = 'admin'，is_admin = 0 -> role = 'teacher'
INSERT INTO users_new (
    id, username, password_hash, salt, name, 
    role, assigned_class, is_active, login_fail_count, 
    locked_until, last_login_ip, last_login, created_at
)
SELECT 
    id,
    username,
    password_hash,
    salt,
    name,
    CASE 
        WHEN is_admin = 1 THEN 'admin'
        ELSE 'teacher'
    END as role,
    NULL as assigned_class,  -- 旧数据没有，需要手动分配
    1 as is_active,          -- 默认激活
    0 as login_fail_count,   -- 默认0次失败
    NULL as locked_until,
    NULL as last_login_ip,
    last_login,
    created_at
FROM users;

-- 删除旧表，重命名新表
DROP TABLE users;
ALTER TABLE users_new RENAME TO users;

-- ============================================
-- 2. checkin_records 表迁移（record_id -> id，添加字段）
-- ============================================

-- 创建新 checkin_records 表
CREATE TABLE checkin_records_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    student_name TEXT,
    class_name TEXT,
    checkin_type TEXT DEFAULT 'self',
    checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 迁移数据（尝试从 students 表获取学生姓名和班级）
INSERT INTO checkin_records_new (
    student_id,
    student_name,
    class_name,
    checkin_type,
    checkin_time
)
SELECT 
    c.student_id,
    s.name as student_name,
    s.class_name,
    COALESCE(c.checkin_type, 'self') as checkin_type,
    c.checkin_time
FROM checkin_records c
LEFT JOIN students s ON c.student_id = s.student_id;

-- 删除旧表，重命名新表
DROP TABLE checkin_records;
ALTER TABLE checkin_records_new RENAME TO checkin_records;

-- ============================================
-- 3. score_logs 表迁移（完全重构结构）
-- ============================================

-- 创建新 score_logs 表
CREATE TABLE score_logs_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    old_score REAL,
    new_score REAL,
    delta REAL,
    reason TEXT,
    operator TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 迁移数据（尝试从旧数据推算 old_score 和 new_score）
-- 旧数据只有 score_change，假设当前分数为基准推算
INSERT INTO score_logs_new (
    student_id,
    old_score,
    new_score,
    delta,
    reason,
    operator,
    created_at
)
SELECT 
    s.student_id,
    NULL as old_score,  -- 无法从旧数据得知，设为NULL
    NULL as new_score,  -- 无法从旧数据得知，设为NULL
    CAST(s.score_change AS REAL) as delta,
    s.reason,
    NULL as operator,   -- 旧数据没有记录操作人
    COALESCE(s.operation_time, datetime('now')) as created_at
FROM score_logs s;

-- 删除旧表，重命名新表
DROP TABLE score_logs;
ALTER TABLE score_logs_new RENAME TO score_logs;

-- ============================================
-- 4. students 表修改（score INTEGER -> REAL）
-- ============================================

-- 创建新 students 表
CREATE TABLE students_new (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    class_name TEXT DEFAULT '未分班',
    score REAL DEFAULT 70.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 迁移数据（score 从 INTEGER 转为 REAL）
INSERT INTO students_new (
    student_id,
    name,
    class_name,
    score,
    created_at
)
SELECT 
    student_id,
    name,
    COALESCE(class_name, '未分班') as class_name,
    CAST(score AS REAL) as score,
    created_at
FROM students;

-- 删除旧表，重命名新表
DROP TABLE students;
ALTER TABLE students_new RENAME TO students;

-- ============================================
-- 5. 删除旧 class_session 表（新代码未使用）
-- ============================================
-- 注意：如果class_session表中有重要数据，请先备份
-- DROP TABLE IF EXISTS class_session;

-- ============================================
-- 6. 创建新表（如果不存在）
-- ============================================

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_name TEXT,
    role TEXT,
    action TEXT,
    resource TEXT,
    resource_id TEXT,
    method TEXT,
    params TEXT,
    ip_address TEXT,
    user_agent TEXT,
    status_code INTEGER,
    response_msg TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 安全告警表
CREATE TABLE IF NOT EXISTS security_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT,
    severity TEXT,
    description TEXT,
    related_user_id INTEGER,
    related_ip TEXT,
    is_resolved INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 迁移记录表
CREATE TABLE IF NOT EXISTS db_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- ============================================
-- 7. 创建索引
-- ============================================

-- users 表索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- checkin_records 表索引
CREATE INDEX IF NOT EXISTS idx_checkin_student ON checkin_records(student_id);
CREATE INDEX IF NOT EXISTS idx_checkin_time ON checkin_records(checkin_time);
CREATE INDEX IF NOT EXISTS idx_checkin_class ON checkin_records(class_name);

-- score_logs 表索引
CREATE INDEX IF NOT EXISTS idx_score_student ON score_logs(student_id);
CREATE INDEX IF NOT EXISTS idx_score_time ON score_logs(created_at);

-- students 表索引
CREATE INDEX IF NOT EXISTS idx_students_class ON students(class_name);

-- audit_logs 表索引
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);

-- security_alerts 表索引
CREATE INDEX IF NOT EXISTS idx_alert_type ON security_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_resolved ON security_alerts(is_resolved);

-- ============================================
-- 8. 记录迁移版本
-- ============================================
INSERT OR REPLACE INTO db_migrations (version, description) 
VALUES ('2.0.0', 'Migrate from old schema to new DDD schema');

COMMIT;

PRAGMA foreign_keys = ON;

-- 迁移完成提示
SELECT 'Migration completed successfully!' as status;
SELECT 'Users migrated: ' || COUNT(*) FROM users;
SELECT 'Students migrated: ' || COUNT(*) FROM students;
SELECT 'Checkin records migrated: ' || COUNT(*) FROM checkin_records;
SELECT 'Score logs migrated: ' || COUNT(*) FROM score_logs;
