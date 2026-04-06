-- CourseSession 迁移脚本：从旧 class_session 结构迁移到 course_sessions
-- 适用数据库：SQLite
-- 执行前请务必备份数据库

-- 1. 创建 course_sessions 表
CREATE TABLE IF NOT EXISTS course_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  schedule_id INTEGER,
  session_code VARCHAR(16) NOT NULL,
  course_name VARCHAR(100),
  class_name VARCHAR(100) NOT NULL,
  classroom VARCHAR(50),
  teacher_id INTEGER NOT NULL,
  teacher_name VARCHAR(50),
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  week_number INTEGER,
  status VARCHAR(20) DEFAULT 'active',
  source_type VARCHAR(20) DEFAULT 'manual',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 创建 schedule_adjustments 表
CREATE TABLE IF NOT EXISTS schedule_adjustments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  schedule_id INTEGER NOT NULL,
  week_number INTEGER NOT NULL,
  type VARCHAR(20) NOT NULL,
  new_date DATE,
  new_start_time VARCHAR(10),
  new_end_time VARCHAR(10),
  new_classroom VARCHAR(50),
  generated_session_id INTEGER,
  reason VARCHAR(200),
  created_by INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 迁移 class_session 数据到 course_sessions（如果旧表存在）
INSERT INTO course_sessions (
  session_code, class_name, teacher_id, teacher_name,
  course_name, start_time, status, source_type, updated_at
)
SELECT
  UPPER(SUBSTR(HEX(RANDOMBLOB(4)), 1, 8)),
  class_name,
  teacher_id,
  teacher_name,
  course_name,
  start_time,
  CASE WHEN active = 1 THEN 'active' ELSE 'ended' END,
  'manual',
  CURRENT_TIMESTAMP
FROM class_session
WHERE TRUE
ON CONFLICT DO NOTHING;

-- 4. 创建临时映射表用于更新 checkin_records
CREATE TEMP TABLE __session_id_map AS
SELECT
  cs_old.id AS old_id,
  cs_new.id AS new_id
FROM class_session cs_old
JOIN course_sessions cs_new
  ON cs_new.class_name = cs_old.class_name
  AND cs_new.teacher_id = cs_old.teacher_id
  AND (
    cs_old.start_time IS NULL
    OR cs_new.start_time = cs_old.start_time
    OR ABS(STRFTIME('%s', cs_new.start_time) - STRFTIME('%s', cs_old.start_time)) <= 60
  );

-- 5. 更新 checkin_records.session_id
UPDATE checkin_records
SET session_id = (
  SELECT new_id FROM __session_id_map WHERE old_id = checkin_records.session_id
)
WHERE session_id IS NOT NULL
  AND EXISTS (SELECT 1 FROM __session_id_map WHERE old_id = checkin_records.session_id);

-- 6. 删除旧表和临时映射表
DROP TABLE IF EXISTS class_session;
DROP TABLE IF EXISTS __session_id_map;

-- 7. 给 course_schedules 添加 week_type 列
ALTER TABLE course_schedules ADD COLUMN week_type VARCHAR(20) DEFAULT 'all';
