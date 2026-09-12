import { get, post } from '@/lib/api'
import type { CheckinRecord, CheckinRequest, CourseSessionStatus } from '@/types'

export interface CheckinStats {
  active: boolean
  class_name?: string
  total: number
  checked_in: number
  not_checked_in: number
  rate: number
}

export interface ActiveCourseSession {
  id: number                    // 课堂会话ID（用于按课堂查签到统计）
  course_name?: string
  class_name: string
  teacher_name: string
  start_time: string
}

/**
 * 签到管理 API - FE-003 修复后
 *
 * 调用方无需再检查 res.success，错误会自动抛出
 * 返回类型直接是数据 T，而不是 ApiResponse<T>
 */
export const checkinApi = {
  /**
   * 学生签到（带GPS和设备信息）
   */
  checkin: (data: CheckinRequest): Promise<CheckinRecord> =>
    post('/checkin', data),

  /**
   * 获取签到记录列表（admin 用）
   */
  getAll: (limit?: number): Promise<CheckinRecord[]> => {
    const query = limit ? `?limit=${limit}` : ''
    return get(`/checkins${query}`)
  },

  /**
   * 获取指定课堂的签到列表
   */
  getSessionCheckins: (sessionId: number): Promise<CheckinRecord[]> =>
    get(`/checkins/session/${sessionId}`),

  /**
   * 获取签到统计（支持按 session_id）
   */
  getStats: (sessionId?: number): Promise<CheckinStats> => {
    const query = sessionId !== undefined ? `?session_id=${sessionId}` : ''
    return get(`/checkins/stats${query}`)
  },

  /**
   * 获取班级活跃课堂状态（学生端使用）
   */
  getCourseSessionForClass: (classId: number): Promise<CourseSessionStatus> =>
    get(`/course-sessions/class/${classId}`),

  /**
   * 获取所有活跃课堂列表（管理员Dashboard使用）
   */
  getActiveSessions: (): Promise<ActiveCourseSession[]> =>
    get('/course-sessions/active'),
}
