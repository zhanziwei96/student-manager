import { get, post, put, del } from '@/lib/api'
import type { AdminClass } from '@/types'

/** 创建班级请求 - 对应后端 CreateClassRequest */
export interface CreateClassRequest {
  name: string
  major?: string
  cohort_year: string
}

/** 更新班级请求 - 对应后端 UpdateClassRequest */
export interface UpdateClassRequest {
  name?: string
  major?: string
  status?: 'active' | 'archived'
}

/**
 * 班级管理 API（管理员 CRUD）
 *
 * 后端路由: backend/app/api/routes/classes.py
 */
export const classesApi = {
  /** 班级列表（可按届过滤，含学生数；默认只返回在用班级） */
  list: (cohortYear?: string, includeArchived = false): Promise<AdminClass[]> =>
    get('/classes', {
      ...(cohortYear ? { cohort_year: cohortYear } : {}),
      ...(includeArchived ? { include_archived: true } : {}),
    }),

  create: (data: CreateClassRequest): Promise<AdminClass> =>
    post('/classes', data),

  update: (id: number, data: UpdateClassRequest): Promise<AdminClass> =>
    put(`/classes/${id}`, data),

  delete: (id: number): Promise<void> =>
    del(`/classes/${id}`),
}
