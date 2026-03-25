import { get, post } from '@/lib/api'
import type { ClassSession, StartClassRequest } from '@/types'

export interface ActiveClassSession {
  class_name: string
  teacher_id: number
  teacher_name: string
  start_time: string
}

/**
 * 课堂会话 API - FE-003 修复后
 *
 * 调用方无需再检查 res.success，错误会自动抛出
 * 返回类型直接是数据 T，而不是 ApiResponse<T>
 */
export const classSessionApi = {
  getCurrent: (): Promise<ClassSession | null> =>
    get('/class-session'),

  start: (data: StartClassRequest): Promise<ClassSession> =>
    post('/class-session/start', data),

  end: (): Promise<ClassSession> =>
    post('/class-session/end'),

  getStudents: (): Promise<{
    students: Array<{
      id: number
      student_id: string
      name: string
      checked_in: boolean
      checkin_time?: string
    }>
  }> =>
    get('/class-session/students'),

  getActiveSessions: (): Promise<ActiveClassSession[]> =>
    get('/class-sessions/active'),
}
