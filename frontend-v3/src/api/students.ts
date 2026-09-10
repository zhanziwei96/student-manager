import { get, post, put, del, requestRaw } from '@/lib/api'
import type {
  Student,
  StudentStatus,
  CreateStudentRequest,
} from '@/types'

/** 学生列表分页参数 */
export interface StudentListParams {
  class_name?: string
  limit?: number
  offset?: number
}

/** 学生列表分页结果 */
export interface StudentPage {
  items: Student[]
  total: number
}

/**
 * 学生相关 API - FE-003 修复后
 *
 * 调用方无需再检查 res.success，错误会自动抛出
 * 返回类型直接是数据 T，而不是 ApiResponse<T>
 */
export const studentsApi = {
  getAll: (): Promise<Student[]> =>
    get('/students'),

  /**
   * 分页获取学生列表（服务端分页）
   *
   * 不传 limit 时后端返回全部且不带 total（向后兼容），
   * 此时前端以 items.length 作为 total 回退值。
   */
  getPaginated: async (params?: StudentListParams): Promise<StudentPage> => {
    const res = await requestRaw<Student[]>('/students', {
      query: (params ?? {}) as Record<string, unknown>,
    })
    const items = res.data ?? []
    return { items, total: res.total ?? items.length }
  },

  getById: (id: number): Promise<Student> =>
    get(`/students/${id}`),

  getByStudentId: (studentId: string): Promise<Student> =>
    get(`/students/${studentId}`),

  /** 按班级名获取学生列表 */
  getStudentsByClass: (className: string): Promise<Student[]> =>
    get('/students', { class_name: className }),

  create: (data: CreateStudentRequest): Promise<Student> =>
    post('/students', data),

  delete: (id: number): Promise<void> =>
    del(`/students/${id}`),

  resetPassword: (id: number, newPassword: string): Promise<void> =>
    put(`/students/${id}/reset-password`, { new_password: newPassword }),

  /** 按班级批量禁用学生账号（学期归档，admin 或负责该班的教师），支持一次传多个班级 */
  disableByClass: (classNames: string[]): Promise<{ disabled_count: number; class_names: string[] }> =>
    post('/students/disable-by-class', { class_names: classNames }),

  /** 学籍状态管理（在读/休学/退学/毕业，仅管理员） */
  updateStatus: (studentId: string, status: StudentStatus): Promise<void> =>
    put(`/students/${studentId}/status`, { status }),

  /** 学生转班（仅管理员） */
  transferClass: (studentId: string, classId: number): Promise<void> =>
    put(`/students/${studentId}/class`, { class_id: classId }),

  import: (file: File): Promise<{ imported: number }> => {
    const formData = new FormData()
    formData.append('file', file)
    return post('/students/import', formData)
  },
}
