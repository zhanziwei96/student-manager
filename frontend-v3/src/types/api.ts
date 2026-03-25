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

export interface User {
  id: number
  username: string
  name: string
  role: UserRole
  is_admin?: boolean
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

// 学生类型
export interface Student {
  id: number
  student_id: string
  name: string
  class_name: string
  score: number
  status: 'active' | 'inactive'
}

export interface CreateStudentRequest {
  student_id: string
  name: string
  class_name: string
  initial_score?: number
}

export interface UpdateScoreRequest {
  score_change: number
  reason: string
}

export interface ScoreLog {
  id: number
  student_id: number
  score_change: number
  reason: string
  created_at: string
  created_by: string
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
  class_name: string
  start_time: string
  teacher_id: number
  teacher_name?: string
  active: boolean
  checked_in_count?: number
}

export interface StartClassRequest {
  class_name: string
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

// 班级信息类型
export interface ClassInfo {
  id: number
  name: string
  teacher: string
  students: number
  schedule: string
  status: 'active' | 'inactive'
}
