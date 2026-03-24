import { api } from '@/lib/api'
import type { ApiResponse, CheckinRecord } from '@/types'

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
}

export interface ClassSessionStatus {
  id?: number
  session_code?: string
  active: boolean
  class_name?: string
  teacher_name?: string
  start_time?: string
}

/**
 * 签到管理 API
 */
export const checkinApi = {
  /**
   * 学生签到
   */
  checkin: (data: CheckinRequest): Promise<ApiResponse<CheckinRecord>> =>
    api('/checkin', { method: 'POST', body: data }),

  /**
   * 获取今日签到列表
   */
  getToday: (className?: string): Promise<ApiResponse<CheckinRecord[]>> =>
    api(`/checkins/today${className ? `?class_name=${encodeURIComponent(className)}` : ''}`, { method: 'GET' }),

  /**
   * 获取签到统计
   */
  getStats: (): Promise<ApiResponse<CheckinStats>> =>
    api('/checkins/stats', { method: 'GET' }),

  /**
   * 获取班级活跃课堂状态（学生端使用）
   */
  getClassSessionForClass: (className: string): Promise<ApiResponse<ClassSessionStatus>> =>
    api(`/class-sessions/class/${encodeURIComponent(className)}`, { method: 'GET' }),
}
