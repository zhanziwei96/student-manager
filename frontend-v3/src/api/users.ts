import { get, post, put, del } from '@/lib/api'
import type { User } from '@/types'

export interface CreateTeacherRequest {
  username: string
  password: string
  name: string
  role: string
  assigned_classes?: string[]
}

export interface UpdateTeacherRequest {
  name?: string
  role?: string
  assigned_classes?: string[]
  is_account_enabled?: boolean
}

/**
 * 用户管理 API - FE-003 修复后
 *
 * 调用方无需再检查 res.success，错误会自动抛出
 * 返回类型直接是数据 T，而不是 ApiResponse<T>
 */
export const usersApi = {
  getAll: (role?: string): Promise<User[]> => {
    const url = role ? `/admin/users?role=${role}` : '/admin/users'
    return get(url)
  },

  getTeachers: (): Promise<User[]> =>
    get('/admin/users?role=teacher'),

  create: (data: CreateTeacherRequest): Promise<User> =>
    post('/admin/users', data),

  update: (id: number, data: UpdateTeacherRequest): Promise<User> =>
    put(`/admin/users/${id}`, data),

  delete: (id: number): Promise<void> =>
    del(`/admin/users/${id}`),

  resetPassword: (id: number, newPassword: string): Promise<void> =>
    put(`/admin/users/${id}/reset-password`, { new_password: newPassword }),
}
