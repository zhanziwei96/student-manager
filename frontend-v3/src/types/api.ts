// API Response wrapper
export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
}

// User types
export type UserRole = 'admin' | 'teacher' | 'student'

export interface User {
  id: number
  username: string
  name: string
  role: UserRole
  is_admin?: boolean
}

// Auth types
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

// Student types
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

// Stats types
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

// Class Session types
export interface ClassSession {
  id: string
  class_name: string
  start_time: string
  teacher_id: number
  checked_in_count?: number
}

export interface StartClassRequest {
  class_name: string
}

// Check-in types
export interface CheckinRequest {
  student_code: string
  session_id: string
}

export interface CheckInRequest {
  student_code: string
  session_id: string
}

export interface CheckinRecord {
  id: number
  student_id: number
  student_name: string
  session_id: string
  check_in_time: string
  points_earned: number
}

export interface CheckInResponse {
  success: boolean
  message: string
  student_id?: string
  student_name?: string
  points_earned?: number
}
