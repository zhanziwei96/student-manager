/**
 * 课表 API
 * 
 * REVIEW-P1: 统一使用 request<T>() 包装，返回类型为 T（已自动提取 data）
 * 与 lib/api.ts 中的 get/post/del 函数保持一致
 */
import { get, put, del } from '@/lib/api'

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
   * 返回类型: CourseSchedule[]（已自动提取 data）
   */
  getList: (params?: {
    class_name?: string
    teacher_id?: number
    day_of_week?: number
  }): Promise<CourseSchedule[]> =>
    get('/schedules', params),

  /**
   * 获取今日课表
   * 返回类型: CourseSchedule[]（已自动提取 data）
   */
  getToday: (): Promise<CourseSchedule[]> =>
    get('/schedules/today'),

  /**
   * 导入课表
   * 使用原生 fetch 处理文件上传，避免 ofetch 的 Content-Type 问题
   * 返回提取后的 ImportResult（与 request<T>() 行为一致）
   */
  import: async (file: File): Promise<ImportResult> => {
    const formData = new FormData()
    formData.append('file', file)
    
    const res = await fetch('/api/v1/schedules/import', {
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
      teacher_name: teacherName
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
    get('/schedules/template', {
      responseType: 'blob'
    })
}
