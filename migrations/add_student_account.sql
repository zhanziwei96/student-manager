-- ============================================
-- 为学生表添加账号字段
-- ============================================

-- 开启外键约束检查
PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- 1. 为学生表添加账号相关字段
-- 学生使用学号作为用户名，不需要单独的 username 字段
ALTER TABLE students ADD COLUMN password_hash TEXT;
ALTER TABLE students ADD COLUMN salt TEXT;
ALTER TABLE students ADD COLUMN is_active INTEGER DEFAULT 1;

-- 2. 添加最后登录时间字段
ALTER TABLE students ADD COLUMN last_login TIMESTAMP;

COMMIT;

PRAGMA foreign_keys = ON;

-- 完成提示
SELECT 'Student account fields added successfully!' as status;
