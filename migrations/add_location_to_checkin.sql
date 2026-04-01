-- 添加地理位置和设备信息到签到系统
-- 执行时间: 2026-04-01

-- ClassSession 表添加位置字段
ALTER TABLE class_session ADD COLUMN location_lat REAL;
ALTER TABLE class_session ADD COLUMN location_lng REAL;
ALTER TABLE class_session ADD COLUMN location_name TEXT;
ALTER TABLE class_session ADD COLUMN checkin_radius INTEGER DEFAULT 100;

-- CheckinRecord 表添加位置和设备字段
ALTER TABLE checkin_records ADD COLUMN checkin_lat REAL;
ALTER TABLE checkin_records ADD COLUMN checkin_lng REAL;
ALTER TABLE checkin_records ADD COLUMN checkin_distance REAL;
ALTER TABLE checkin_records ADD COLUMN device_id TEXT;
ALTER TABLE checkin_records ADD COLUMN device_info TEXT;

-- 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_checkin_device_session ON checkin_records(device_id, session_id);
CREATE INDEX IF NOT EXISTS idx_class_session_location ON class_session(location_lat, location_lng);
