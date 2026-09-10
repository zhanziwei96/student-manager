/**
 * API 类型定义 - FE-004 修复：与后端模型同步
 *
 * 后端模型位置: backend/app/models/
 * 修改类型时请参考后端对应模型，确保字段一致
 */

// API 响应包装器
export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  /** 分页请求时后端返回的总数（仅部分列表接口） */
  total?: number
}

// 用户角色常量 - FE-002 修复: 避免硬编码字符串
export const UserRoleConst = {
  ADMIN: 'admin' as const,
  TEACHER: 'teacher' as const,
  STUDENT: 'student' as const,
} as const

// 用户类型
export type UserRole = 'admin' | 'teacher' | 'student'

/**
 * 用户类型 - 对应后端 UserResponse
 *
 * 后端模型: backend/app/models/user.py::UserResponse
 * 注意: 保持与后端字段一致，修改时需同步更新
 */
export interface User {
  id: number                    // 用户ID
  username: string              // 用户名
  name: string                  // 姓名
  role: UserRole                // 角色
  class_name?: string           // 学生所属班级
  is_account_enabled: boolean   // 账户是否启用
  last_login?: string           // 最后登录时间（ISO格式）
  created_at?: string           // 创建时间（ISO格式）
}

/**
 * 创建用户请求 - 对应后端 UserCreate
 *
 * 后端模型: backend/app/models/user.py::UserCreate
 */
export interface CreateUserRequest {
  username: string              // 用户名
  password: string              // 密码
  name: string                  // 姓名
  role: UserRole                // 角色
}

/**
 * 更新用户请求 - 对应后端 UserUpdate
 *
 * 后端模型: backend/app/models/user.py::UserUpdate
 */
export interface UpdateUserRequest {
  name?: string                 // 姓名（可选）
  role?: UserRole               // 角色（可选）
  is_account_enabled?: boolean  // 账户是否启用（可选）
}

// 认证类型
export interface LoginRequest {
  username: string
  password: string
  role: UserRole
}

export interface LoginResponse {
  id: number
  username: string
  name: string
  role: UserRole
  is_admin: boolean
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

/**
 * 学生类型 - 对应后端 StudentResponse
 *
 * 后端模型: backend/app/models/student.py::StudentResponse
 * 注意: 保持与后端字段一致，修改时需同步更新
 */
export interface Student {
  id?: number                   // 内部ID（后端可能返回 null 或不存在此字段）
  student_id: string            // 学号（业务主键）
  name: string                  // 姓名
  class_name: string            // 班级
  status?: StudentStatus        // 学籍状态（active|suspended|withdrawn|graduated）
  is_account_enabled: boolean   // 账户是否启用
  checkin_status?: 'checked_in' | 'not_checked_in' // 课堂签到状态（API 动态返回）
  created_at?: string           // 创建时间（ISO格式）
  last_login?: string           // 最后登录时间（ISO格式）
}

// 学籍状态 - 对应后端 Student.status
export type StudentStatus = 'active' | 'suspended' | 'withdrawn' | 'graduated'

/**
 * 创建学生请求 - 对应后端 StudentCreate
 *
 * 后端模型: backend/app/models/student.py::StudentCreate
 */
export interface CreateStudentRequest {
  student_id: string            // 学号
  name: string                  // 姓名
  class_name: string            // 班级
}

/**
 * 更新学生请求 - 对应后端 StudentUpdate
 *
 * 后端模型: backend/app/models/student.py::StudentUpdate
 */
export interface UpdateStudentRequest {
  name?: string                 // 姓名（可选）
  class_name?: string           // 班级（可选）
  // 注意：后端 StudentUpdate 不支持修改账户状态
}

// 统计类型
export interface StatsData {
  total_students: number
  active_students: number
  total_classes: number
}

export interface DashboardData {
  stats: StatsData
  recent_activity: Array<{
    id: number
    type: string
    description: string
    created_at: string
  }>
  top_students: Student[]
}

// 签到类型
export interface CheckinRequest {
  student_id: string
  student_name: string
  device_id?: string
  device_info?: string
  verification_code?: string
  session_id?: number
}

export interface CheckinRecord {
  id: number
  session_id?: number
  student_id: string
  student_name: string
  class_name: string
  checkin_time: string
  checkin_type?: string
  device_id?: string
  device_info?: string
}

export interface CourseSessionStatus {
  id?: number
  session_code?: string
  active: boolean
  class_name?: string
  teacher_name?: string
  start_time?: string
}

/**
 * 班级类型 - 对应后端 classes 路由 _class_dict
 *
 * 后端模型: backend/app/api/routes/classes.py
 * 注意: 保持与后端字段一致，修改时需同步更新
 */
export interface AdminClass {
  id: number                    // 班级ID
  name: string                  // 班级名（如 1班）
  major: string                 // 专业
  cohort_year: string           // 所属届
  display_name: string          // 显示名（届+专业+班）
  student_count: number         // 学生数
}

/**
 * 学期类型 - 对应后端 semesters 路由 _semester_dict
 *
 * 后端模型: backend/app/api/routes/semesters.py
 */
export interface Semester {
  id: number                    // 学期ID
  label: string                 // 学期标识（如 2026-2027-1）
  start_date: string            // 开学第一天（ISO格式）
  total_weeks: number           // 总周数
  is_current: boolean           // 是否当前学期
  status: 'active' | 'archived' // 状态
}

/**
 * 届类型 - 对应后端 cohorts 路由 _cohort_dict
 *
 * 后端模型: backend/app/api/routes/cohorts.py
 */
export interface Cohort {
  year: string                  // 届（入学年份，如 2026）
  label: string                 // 显示名（如 2026届）
  entry_semester_id: number | null // 入学学期ID
  status: 'active' | 'graduated'   // 状态
}

/**
 * 课程类型 - 对应后端 courses 路由 _course_dict
 *
 * 后端模型: backend/app/api/routes/courses.py
 */
export interface Course {
  id: number                    // 课程ID
  code: string                  // 课程编码（如 MATH1001）
  name: string                  // 课程名称
  department: string            // 开课院系
  status: 'active' | 'archived' // 状态
}

/**
 * 教学班类型 - 对应后端 offerings 路由 _offering_dict
 *
 * 后端模型: backend/app/api/routes/course_offerings.py
 */
export interface CourseOffering {
  id: number                    // 教学班ID
  course_id: number             // 课程ID
  semester_id: number           // 学期ID
  teacher_id: number | null     // 教师ID（可空：先排课后定教师）
  teacher_name: string          // 教师姓名
  class_scope: string           // 面向范围（如 计科1-2班）
  capacity: number | null       // 容量
  status: 'active' | 'ended'    // 状态
}

/**
 * 选课名单行 - 对应后端 offerings/{id}/enrollments 响应
 *
 * 后端模型: backend/app/api/routes/course_offerings.py::list_offering_enrollments
 */
export interface EnrollmentRow {
  enrollment_id: number         // 选课记录ID
  student_id: string            // 学号
  name: string                  // 姓名
  class_name: string            // 班级
  score: number                 // 平时成绩
  final_score: number | null    // 期末成绩
}

// 排行榜类型
export interface LeaderboardStudent {
  rank: number
  student_id: string
  name: string
  class_name: string
  score: number
}

export interface LeaderboardData {
  scope: 'class' | 'school'
  students: LeaderboardStudent[]
  total: number
  my_rank: {
    rank: number
    student_id: string
    name: string
    score: number
  } | null
}

// 课程会话类型（新表 course_sessions）
export interface CourseSession {
  id: number
  session_code: string
  course_name?: string
  class_name: string
  classroom?: string
  teacher_id: number
  teacher_name?: string
  start_time: string
  end_time?: string
  status: 'active' | 'ended' | 'cancelled'
  week_number?: number
  schedule_id?: number
  source_type: 'scheduled' | 'manual' | 'makeup'
}

export interface StartCourseSessionRequest {
  class_name: string
  course_name?: string
  schedule_id?: number
}

// 课表调整记录
export interface ScheduleAdjustment {
  id: number
  schedule_id: number
  week_number: number
  type: 'cancel' | 'modify' | 'makeup'
  reason?: string
  new_date?: string
  new_start_time?: string
  new_end_time?: string
  new_classroom?: string
  generated_session_id?: number
  created_by: number
  created_at: string
}

export interface CreateScheduleAdjustmentRequest {
  schedule_id: number
  week_number: number
  type: 'cancel' | 'modify' | 'makeup'
  reason?: string
  new_date?: string
  new_start_time?: string
  new_end_time?: string
  new_classroom?: string
}

// 今日课表增强类型
export interface TodayScheduleItem {
  id: number
  course_name: string
  class_name: string
  teacher_id?: number
  teacher_name?: string
  day_of_week: number
  start_time: string
  end_time: string
  classroom?: string
  week_start: number
  week_end: number
  week_type: string
  week_number: number
  week_type_match: boolean
  session_status: 'none' | 'active' | 'ended' | 'cancelled' | 'adjusted' | 'makeup' | 'skipped'
  active_session_id?: number
  adjustment?: {
    type: string
    reason?: string
    new_date?: string
    new_start_time?: string
    new_end_time?: string
    new_classroom?: string
  }
}

// 小组成员详情
export interface GroupMember {
  student_id: string
  student_name: string
  joined_at: string
}

// 小组详情（含成员列表）
export interface GroupDetail {
  id: number
  class_name: string
  name: string
  leader_student_id: string
  is_active: boolean
  created_at: string
  members: GroupMember[]
}
