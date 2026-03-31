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
  assigned_classes?: string[]   // 负责班级列表（FE-004: 补充缺失字段）
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
  assigned_classes?: string[]   // 负责班级列表（可选）
}

/**
 * 更新用户请求 - 对应后端 UserUpdate
 *
 * 后端模型: backend/app/models/user.py::UserUpdate
 */
export interface UpdateUserRequest {
  name?: string                 // 姓名（可选）
  role?: UserRole               // 角色（可选）
  assigned_classes?: string[]   // 负责班级列表（可选）
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
  id: number                    // 内部ID
  student_id: string            // 学号（业务主键）
  name: string                  // 姓名
  class_name: string            // 班级
  score: number                 // 分数
  is_account_enabled: boolean   // 账户是否启用
  checkin_status?: 'checked_in' | 'not_checked_in' // 课堂签到状态（API 动态返回）
  created_at?: string           // 创建时间（ISO格式）
  last_login?: string           // 最后登录时间（ISO格式）
}

/**
 * 创建学生请求 - 对应后端 StudentCreate
 *
 * 后端模型: backend/app/models/student.py::StudentCreate
 */
export interface CreateStudentRequest {
  student_id: string            // 学号
  name: string                  // 姓名
  class_name: string            // 班级
  score?: number                // 初始分数（可选，默认70）
}

/**
 * 更新学生请求 - 对应后端 StudentUpdate
 *
 * 后端模型: backend/app/models/student.py::StudentUpdate
 */
export interface UpdateStudentRequest {
  name?: string                 // 姓名（可选）
  class_name?: string           // 班级（可选）
  score?: number                // 分数（可选）
  // 注意：后端 StudentUpdate 不支持修改账户状态
}

export interface UpdateScoreRequest {
  score_change: number
  reason: string
}

export interface ScoreLog {
  id: number
  student_id: string
  old_score: number | null
  new_score: number | null
  delta: number
  reason: string | null
  operator: string | null
  created_at: string
}

// 统计类型
export interface StatsData {
  total_students: number
  active_students: number
  total_classes: number
  average_score: number
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

// 课堂会话类型
export interface ClassSession {
  id: string
  course_name?: string
  class_name: string
  start_time: string
  teacher_id: number
  teacher_name?: string
  active: boolean
  checked_in_count?: number
}

export interface StartClassRequest {
  class_name: string
  course_name?: string
}

// 签到类型
export interface CheckinRequest {
  student_code: string
  session_id: string
}

export interface CheckinRecord {
  id: number
  session_id?: number
  student_id: string
  student_name: string
  class_name: string
  checkin_time: string
  checkin_type?: string
}

/**
 * 班级信息类型 - 对应后端 ClassInfo
 *
 * 注意: 与后端返回的班级数据结构保持一致
 */
export interface ClassInfo {
  name: string
  status: 'active' | 'inactive'
  student_count?: number        // 学生数量（由前端计算）
  average_score?: number        // 平均分（由前端计算）
}

/**
 * 班级详细信息 - 包含统计数据
 */
export interface ClassWithStats extends ClassInfo {
  student_count: number
  average_score: number
}
