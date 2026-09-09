import { get, post, put } from '@/lib/api'
import type { Semester } from '@/types'

/** 创建学期请求 - 对应后端 CreateSemesterRequest */
export interface CreateSemesterRequest {
  label: string
  start_date: string
  total_weeks: number
}

/** 更新学期请求 - 对应后端 UpdateSemesterRequest */
export interface UpdateSemesterRequest {
  start_date?: string
  total_weeks?: number
  status?: 'active' | 'archived'
}

/**
 * 学期管理 API（管理员）
 *
 * 后端路由: backend/app/api/routes/semesters.py
 */
export const semestersApi = {
  list: (): Promise<Semester[]> =>
    get('/semesters'),

  create: (data: CreateSemesterRequest): Promise<Semester> =>
    post('/semesters', data),

  update: (id: number, data: UpdateSemesterRequest): Promise<Semester> =>
    put(`/semesters/${id}`, data),

  /** 切换当前学期 */
  activate: (id: number): Promise<void> =>
    post(`/semesters/${id}/activate`),

  /** 学期 rollover：复制归属/开课/选课到当前学期 */
  rollover: (): Promise<void> =>
    post('/semesters/rollover'),
}
