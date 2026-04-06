import { get, post } from '@/lib/api'
import type { CheckinRecord } from '@/types'

export interface CheckinStats {
  active: boolean
  class_name?: string
  total: number
  checked_in: number
  not_checked_in: number
  rate: number
}

export interface CheckinRequest {
  student_id: string
  student_name: string
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

export interface ActiveCourseSession {
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
   * 获取今日签到列表
   */
  getToday: (className?: string): Promise<CheckinRecord[]> => {
    const query = className ? `?class_name=${encodeURIComponent(className)}` : ''
    return get(`/checkins/today${query}`)
  },

  /**
   * 获取签到统计
   */
  getStats: (): Promise<CheckinStats> =>
    get('/checkins/stats'),

  /**
   * 获取班级活跃课堂状态（学生端使用）
   */
  getCourseSessionForClass: (className: string): Promise<CourseSessionStatus> =>
    get(`/course-sessions/class/${encodeURIComponent(className)}`),

  /**
   * 获取所有活跃课堂列表（管理员Dashboard使用）
   */
  getActiveSessions: (): Promise<ActiveCourseSession[]> =>
    get('/course-sessions/active'),
}
