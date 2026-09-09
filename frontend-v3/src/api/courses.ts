import { get, post, put } from '@/lib/api'
import type { Course } from '@/types'

/** 创建课程请求 - 对应后端 CreateCourseRequest */
export interface CreateCourseRequest {
  code: string
  name: string
  department?: string
}

/** 更新课程请求 - 对应后端 UpdateCourseRequest */
export interface UpdateCourseRequest {
  name?: string
  department?: string
  status?: 'active' | 'archived'
}

/**
 * 课程目录 API（管理员）
 *
 * 后端路由: backend/app/api/routes/courses.py
 */
export const coursesApi = {
  list: (): Promise<Course[]> =>
    get('/courses'),

  create: (data: CreateCourseRequest): Promise<Course> =>
    post('/courses', data),

  update: (id: number, data: UpdateCourseRequest): Promise<Course> =>
    put(`/courses/${id}`, data),
}
