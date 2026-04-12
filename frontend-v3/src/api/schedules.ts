/**
 * 课表 API
 *
 * REVIEW-P1: 统一使用 request<T>() 包装，返回类型为 T（已自动提取 data）
 * 与 lib/api.ts 中的 get/post/del 函数保持一致
 */
import { get, put, del, api, post } from '@/lib/api'
import type { TodayScheduleItem } from '@/types'

export interface CourseSchedule {
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
  created_at?: string
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
  is_virtual?: boolean
  parent_schedule_id?: number
  has_makeup?: boolean
  parent_adjustment_reason?: string
}

export interface ImportResult {
  imported: number
  errors: string[]
}

export const schedulesApi = {
  /**
   * 获取课表列表
   * 返回类型: CourseSchedule[]（已自动提取 data）
   */
  getList: (params?: {
    class_name?: string
    teacher_id?: number
    day_of_week?: number
    week_number?: number
  }): Promise<CourseSchedule[]> =>
    get('/schedules', params),

  /**
   * 获取今日课表
   * 返回类型: TodayScheduleItem[]（已自动提取 data）
   */
  getToday: (): Promise<TodayScheduleItem[]> =>
    get('/schedules/today'),

  /**
   * 导入课表
   * 通过 ofetch 的 FormData 自动处理 multipart boundary
   * 返回提取后的 ImportResult（与 request<T>() 行为一致）
   */
  import: async (file: File): Promise<ImportResult> => {
    const formData = new FormData()
    formData.append('file', file)
    return post<ImportResult, FormData>('/schedules/import', formData)
  },

  /**
   * 删除课程
   * 返回类型: void（已自动提取 data）
   */
  delete: (id: number): Promise<void> =>
    del(`/schedules/${id}`),

  /**
   * 为课程分配教师
   * 返回类型: void（已自动提取 data）
   */
  assign: (id: number, teacherId: number, teacherName: string): Promise<void> =>
    put(`/schedules/${id}/assign`, null, {
      teacher_id: teacherId,
      teacher_name: teacherName,
    }),

  /**
   * 取消课程的教师分配
   * 返回类型: void（已自动提取 data）
   */
  unassign: (id: number): Promise<void> =>
    put(`/schedules/${id}/unassign`),

  /**
   * 下载导入模板
   * 返回类型: Blob（原始响应，非 JSON）
   */
  downloadTemplate: (): Promise<Blob> =>
    api('/schedules/template', { method: 'GET', responseType: 'blob' }),
}
