-- ============================================
-- BE-008: 并发保护修复 - 乐观锁版本字段迁移
-- ============================================

-- 1. 为学生表添加 version 字段（乐观锁）
-- 注意：SQLite 支持 ALTER TABLE ADD COLUMN，但需要检查列是否已存在
-- 如果列已存在会报错，请确保没有重复执行

-- 添加 version 字段到 students 表
ALTER TABLE students ADD COLUMN version INTEGER DEFAULT 1;

-- 为现有学生设置默认 version=1
UPDATE students SET version = 1 WHERE version IS NULL;

-- 2. 为用户表添加 version 字段（乐观锁）
ALTER TABLE users ADD COLUMN version INTEGER DEFAULT 1;

-- 为现有用户设置默认 version=1
UPDATE users SET version = 1 WHERE version IS NULL;

-- 3. 添加数据库版本记录
INSERT OR IGNORE INTO db_migrations (version, description) 
VALUES ('1.0.1', 'BE-008: Add optimistic lock version field to students and users');

-- 4. 验证迁移结果
-- SELECT 'Students with version:' as info, COUNT(*) as count FROM students WHERE version IS NOT NULL;
-- SELECT 'Users with version:' as info, COUNT(*) as count FROM users WHERE version IS NOT NULL;

-- 迁移完成
