-- 添加课表功能
-- 创建时间: 2026-03-26

-- 课表表
CREATE TABLE IF NOT EXISTS course_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name VARCHAR(100) NOT NULL,      -- 课程名称
    class_name VARCHAR(100) NOT NULL,       -- 班级名称
    teacher_id INTEGER,                     -- 教师ID（关联users表）
    teacher_name VARCHAR(50),               -- 教师姓名
    day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 1 AND 7),  -- 星期几 (1-7)
    start_time TIME NOT NULL,               -- 开始时间
    end_time TIME NOT NULL,                 -- 结束时间
    classroom VARCHAR(50),                  -- 教室
    week_start INTEGER DEFAULT 1 CHECK(week_start >= 1),     -- 开始周次
    week_end INTEGER DEFAULT 20 CHECK(week_end >= 1),        -- 结束周次
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_schedules_class ON course_schedules(class_name);
CREATE INDEX IF NOT EXISTS idx_schedules_teacher ON course_schedules(teacher_id);
CREATE INDEX IF NOT EXISTS idx_schedules_day ON course_schedules(day_of_week);
CREATE INDEX IF NOT EXISTS idx_schedules_time ON course_schedules(start_time, end_time);

-- 插入示例数据（可选）
-- INSERT INTO course_schedules (course_name, class_name, teacher_name, day_of_week, start_time, end_time, classroom) 
-- VALUES ('计算机基础', '2025康复治疗技术1班', '张老师', 1, '08:00', '09:40', 'A-101');
