import { get, post, put } from '@/lib/api'
import type { Cohort } from '@/types'

/** 创建届请求 - 对应后端 CreateCohortRequest */
export interface CreateCohortRequest {
  year: string
  label?: string
}

/** 更新届请求 - 对应后端 UpdateCohortRequest */
export interface UpdateCohortRequest {
  label?: string
  status?: 'active' | 'graduated'
}

/**
 * 届管理 API（管理员）
 *
 * 后端路由: backend/app/api/routes/cohorts.py
 */
export const cohortsApi = {
  list: (): Promise<Cohort[]> =>
    get('/cohorts'),

  create: (data: CreateCohortRequest): Promise<Cohort> =>
    post('/cohorts', data),

  update: (year: string, data: UpdateCohortRequest): Promise<Cohort> =>
    put(`/cohorts/${year}`, data),
}
