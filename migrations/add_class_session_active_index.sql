-- 添加 class_session 表 active 字段索引
-- 用途: 优化"正在上课"查询性能
-- 背景: admin 仪表盘需要频繁查询活跃课堂，缺少索引导致全表扫描

-- 检查索引是否存在，不存在则创建
CREATE INDEX IF NOT EXISTS idx_session_active ON class_session(active);

-- 验证索引创建
-- sqlite3 backend/app/data/class_system.db ".schema class_session"
