import { get, post } from '@/lib/api'
import type { ClassSessionInfo, StartClassRequest } from '@/types'

export interface ActiveClassSession {
  course_name?: string
  class_name: string
  teacher_id: number
  teacher_name: string
  start_time: string
}

export interface EndClassRequest {
  class_name?: string
}

/**
 * 课堂会话 API - FE-003 修复后
 *
 * 调用方无需再检查 res.success，错误会自动抛出
 * 返回类型直接是数据 T，而不是 ApiResponse<T>
 */
export const classSessionApi = {
  /**
   * 获取当前教师的所有活跃课堂
   * 多班级并行上课支持 - 返回列表
   */
  getCurrent: (): Promise<ClassSessionInfo[]> =>
    get('/class-session'),

  start: (data: StartClassRequest): Promise<ClassSessionInfo> =>
    post('/class-session/start', data),

  /**
   * 结束上课
   * @param data 可选的班级名称，不指定则结束所有活跃课堂
   */
  end: (data: EndClassRequest = {}): Promise<void> =>
    post('/class-session/end', data),

  getActiveSessions: (): Promise<ActiveClassSession[]> =>
    get('/class-sessions/active'),
}
