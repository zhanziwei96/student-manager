-- ============================================
-- 班级管理系统安全方案 - 数据库迁移脚本
-- Phase 1: 基础防护 - 数据库改造
-- ============================================

-- 1. 用户表扩展
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'teacher';
ALTER TABLE users ADD COLUMN assigned_class TEXT;  -- 老师绑定的班级（逗号分隔多个班级）
ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN last_login_ip TEXT;
ALTER TABLE users ADD COLUMN login_fail_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;

-- 2. 为现有用户设置默认角色
-- admin 用户设置为 admin 角色，其他设置为 teacher
UPDATE users SET role = 'admin' WHERE is_admin = 1;
UPDATE users SET role = 'teacher' WHERE is_admin = 0 OR is_admin IS NULL;

-- 3. 权限审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_name TEXT,
    role TEXT,
    action TEXT,           -- 操作类型：read/create/update/delete/login/logout
    resource TEXT,         -- 访问的资源：students/checkin/score等
    resource_id TEXT,      -- 资源标识（如学生ID）
    method TEXT,           -- HTTP方法：GET/POST/DELETE
    params TEXT,           -- 请求参数（JSON字符串）
    ip_address TEXT,
    user_agent TEXT,
    status_code INTEGER,   -- 响应状态码
    response_msg TEXT,     -- 响应消息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 创建审计日志索引
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_ip ON audit_logs(ip_address);

-- 5. 异常行为检测表
CREATE TABLE IF NOT EXISTS security_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT,       -- 告警类型：mass_query/cross_class/after_hours
    severity TEXT,         -- 严重级别：high/medium/low
    description TEXT,      -- 告警描述
    related_user_id INTEGER,
    related_ip TEXT,
    is_resolved INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 创建告警索引
CREATE INDEX IF NOT EXISTS idx_alert_type ON security_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_time ON security_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alert_resolved ON security_alerts(is_resolved);

-- 7. 添加数据库版本记录
CREATE TABLE IF NOT EXISTS db_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR IGNORE INTO db_migrations (version, description) 
VALUES ('1.0.0', 'Initial security tables and user role setup');

-- 迁移完成
