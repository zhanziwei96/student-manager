import { api } from '@/lib/api'
import type { ApiResponse } from '@/types'

/**
 * 班级管理 API
 * 后端路由: /api/classes
 */
export const classesApi = {
  getAll: (): Promise<ApiResponse<string[]>> =>
    api('/classes', { method: 'GET' }),
}
