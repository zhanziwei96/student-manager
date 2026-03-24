import { api } from '@/lib/api'
import type { ApiResponse, Student } from '@/types'

export interface ClassInfo {
  name: string
  student_count: number
  teacher?: string
  status: 'active' | 'inactive'
}

/**
 * 班级管理 API
 */
export const classesApi = {
  getAll: (): Promise<ApiResponse<string[]>> =>
    api('/classes', { method: 'GET' }),
    
  getStudentsByClass: (className: string): Promise<ApiResponse<Student[]>> =>
    api(`/students?class_name=${encodeURIComponent(className)}`, { method: 'GET' }),
}
