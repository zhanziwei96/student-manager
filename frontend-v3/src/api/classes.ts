import { get } from '@/lib/api'
import type { Student } from '@/types'

export interface ClassInfo {
  name: string
  status: 'active' | 'inactive'
}

export interface ClassWithStats {
  name: string
  student_count: number
  teacher?: string
  status: 'active' | 'inactive'
  average_score: number
}

/**
 * 班级管理 API - FE-003 修复后
 *
 * 调用方无需再检查 res.success，错误会自动抛出
 * 返回类型直接是数据 T，而不是 ApiResponse<T>
 */
export const classesApi = {
  getAll: (): Promise<ClassInfo[]> =>
    get('/classes'),

  getStudentsByClass: (className: string): Promise<Student[]> =>
    get('/students', { class_name: className }),
}
