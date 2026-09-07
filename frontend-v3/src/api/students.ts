import { get, post, put, del, requestRaw } from '@/lib/api'
import type {
  Student,
  CreateStudentRequest,
  UpdateScoreRequest,
  ScoreLog,
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

/** 分数日志查询参数 */
export interface ScoreLogParams {
  limit?: number
  offset?: number
}

/** 学生科目分数 */
export interface StudentSubjectScore {
  subject_id: number
  subject_name: string
  teacher_id: number
  teacher_name: string
  score: number
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

  create: (data: CreateStudentRequest): Promise<Student> =>
    post('/students', data),

  delete: (id: number): Promise<void> =>
    del(`/students/${id}`),

  updateScore: (studentId: string, data: UpdateScoreRequest): Promise<Student> =>
    put(`/students/${studentId}/score`, data),

  getScoreLogs: (studentId: string, params?: ScoreLogParams): Promise<ScoreLog[]> =>
    get(`/students/${studentId}/scores`, params ? { ...params } : undefined),

  /** 获取学生当前学期所有科目分数 */
  getSubjects: (studentId: string): Promise<StudentSubjectScore[]> =>
    get(`/students/${studentId}/subjects`),

  /** 更新学生某科目分数（admin 或负责该班的教师） */
  updateSubjectScore: (studentId: string, subjectId: number, scoreChange: number, reason: string): Promise<void> =>
    put(`/students/${studentId}/subjects/${subjectId}/score`, { score_change: scoreChange, reason }),

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
