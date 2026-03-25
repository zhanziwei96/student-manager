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

  getList: (): Promise<Student[]> =>
    get('/students'),

  getById: (id: number): Promise<Student> =>
    get(`/students/${id}`),

  getByStudentId: (studentId: string): Promise<Student> =>
    get(`/students/${studentId}`),

  create: (data: CreateStudentRequest): Promise<Student> =>
    post('/students', data),

  delete: (id: number): Promise<void> =>
    del(`/students/${id}`),

  updateScore: (id: number, data: UpdateScoreRequest): Promise<Student> =>
    put(`/students/${id}/score`, data),

  getScoreLogs: (id: number): Promise<ScoreLog[]> =>
    get(`/students/${id}/scores`),

  resetPassword: (id: number, newPassword: string): Promise<void> =>
    put(`/students/${id}/reset-password`, { new_password: newPassword }),

  import: (file: File): Promise<{ imported: number }> => {
    const formData = new FormData()
    formData.append('file', file)
    return post('/students/import', formData)
  },
}
