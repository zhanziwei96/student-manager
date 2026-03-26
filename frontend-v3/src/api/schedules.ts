/**
 * 课表 API
 */
import { get, post, del } from '@/lib/api'
import type { ApiResponse } from '@/types'

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
}

export interface ImportResult {
  imported: number
  errors: string[]
}

export const schedulesApi = {
  /**
   * 获取课表列表
   */
  getList: (params?: {
    class_name?: string
    teacher_id?: number
    day_of_week?: number
  }): Promise<ApiResponse<CourseSchedule[]>> =>
    get('/schedules', { params }),

  /**
   * 获取今日课表
   */
  getToday: (): Promise<ApiResponse<CourseSchedule[]>> =>
    get('/schedules/today'),

  /**
   * 导入课表
   */
  import: (file: File): Promise<ApiResponse<ImportResult>> => {
    const formData = new FormData()
    formData.append('file', file)
    return post('/schedules/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 删除课程
   */
  delete: (id: number): Promise<ApiResponse<void>> =>
    del(`/schedules/${id}`),

  /**
   * 下载导入模板
   */
  downloadTemplate: (): Promise<Blob> =>
    get('/schedules/template', {
      responseType: 'blob'
    })
}
