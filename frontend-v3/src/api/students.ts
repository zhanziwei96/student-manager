import { api } from '@/lib/api'
import type {
  ApiResponse,
  Student,
  CreateStudentRequest,
  UpdateScoreRequest,
  ScoreLog,
} from '@/types'

export const studentsApi = {
  getAll: (): Promise<ApiResponse<Student[]>> =>
    api('/students', { method: 'GET' }),
  
  getList: (): Promise<ApiResponse<Student[]>> =>
    api('/students', { method: 'GET' }),

  getById: (id: number): Promise<ApiResponse<Student>> =>
    api(`/students/${id}`, { method: 'GET' }),

  create: (data: CreateStudentRequest): Promise<ApiResponse<Student>> =>
    api('/students', { method: 'POST', body: data }),

  delete: (id: number): Promise<ApiResponse<void>> =>
    api(`/students/${id}`, { method: 'DELETE' }),

  updateScore: (id: number, data: UpdateScoreRequest): Promise<ApiResponse<Student>> =>
    api(`/students/${id}/score`, { method: 'PUT', body: data }),

  getScoreLogs: (id: number): Promise<ApiResponse<ScoreLog[]>> =>
    api(`/students/${id}/scores`, { method: 'GET' }),

  resetPassword: (id: number, newPassword: string): Promise<ApiResponse<void>> =>
    api(`/students/${id}/reset-password`, {
      method: 'PUT',
      body: { new_password: newPassword },
    }),

  import: (file: File): Promise<ApiResponse<{ imported: number }>> => {
    const formData = new FormData()
    formData.append('file', file)
    return api('/students/import', {
      method: 'POST',
      body: formData,
    })
  },
}
