import { get, post, put, del } from '@/lib/api'
import type {
  Student,
  CreateStudentRequest,
  UpdateScoreRequest,
  ScoreLog,
} from '@/types'

/**
 * 学生相关 API - FE-003 修复后
 *
 * 调用方无需再检查 res.success，错误会自动抛出
 * 返回类型直接是数据 T，而不是 ApiResponse<T>
 */
export const studentsApi = {
  getAll: (): Promise<Student[]> =>
    get('/students'),

  getById: (id: number): Promise<Student> =>
    get(`/students/${id}`),

  getByStudentId: (studentId: string): Promise<Student> =>
    get(`/students/${studentId}`),

  create: (data: CreateStudentRequest): Promise<Student> =>
    post('/students', data),

  delete: (id: number): Promise<void> =>
    del(`/students/${id}`),

  updateScore: (studentId: string, data: UpdateScoreRequest): Promise<Student> =>
    put(`/students/${studentId}/score`, data),

  getScoreLogs: (studentId: string, limit?: number): Promise<ScoreLog[]> =>
    get(`/students/${studentId}/scores`, limit !== undefined ? { limit } : undefined),

  resetPassword: (id: number, newPassword: string): Promise<void> =>
    put(`/students/${id}/reset-password`, { new_password: newPassword }),

  /** 按班级批量禁用学生账号（学期归档，admin 或负责该班的教师），支持一次传多个班级 */
  disableByClass: (classNames: string[]): Promise<{ disabled_count: number; class_names: string[] }> =>
    post('/students/disable-by-class', { class_names: classNames }),

  import: (file: File): Promise<{ imported: number }> => {
    const formData = new FormData()
    formData.append('file', file)
    return post('/students/import', formData)
  },
}
