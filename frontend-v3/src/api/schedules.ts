/**
 * 课表 API
 */
import { get, post, del } from '@/lib/api'
import { api } from '@/lib/api'
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
   * 使用原生 fetch 处理文件上传，避免 ofetch 的 Content-Type 问题
   * 返回提取后的 ImportResult（类似 api.ts 中 request 函数的处理）
   */
  import: async (file: File): Promise<ImportResult> => {
    const formData = new FormData()
    formData.append('file', file)
    
    const res = await fetch('/api/schedules/import', {
      method: 'POST',
      body: formData,
      credentials: 'include'
    })
    
    const responseData = await res.json().catch(() => ({ 
      success: false, 
      message: '解析响应失败' 
    }))
    
    // HTTP 错误或非成功响应
    if (!res.ok || responseData.success === false) {
      throw new Error(responseData.message || `上传失败: ${res.status}`)
    }
    
    // 提取 data 部分（与 api.ts 中 request 函数行为一致）
    return responseData.data as ImportResult
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
