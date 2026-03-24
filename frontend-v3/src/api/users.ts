import { api } from '@/lib/api'
import type { ApiResponse, User } from '@/types'

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
  is_active?: boolean
}

export const usersApi = {
  getAll: (role?: string): Promise<ApiResponse<User[]>> =>
    api(`/admin/users${role ? `?role=${role}` : ''}`, { method: 'GET' }),

  getTeachers: (): Promise<ApiResponse<User[]>> =>
    api('/admin/users?role=teacher', { method: 'GET' }),

  create: (data: CreateTeacherRequest): Promise<ApiResponse<User>> =>
    api('/admin/users', { method: 'POST', body: data }),

  update: (id: number, data: UpdateTeacherRequest): Promise<ApiResponse<User>> =>
    api(`/admin/users/${id}`, { method: 'PUT', body: data }),

  delete: (id: number): Promise<ApiResponse<void>> =>
    api(`/admin/users/${id}`, { method: 'DELETE' }),

  resetPassword: (id: number, newPassword: string): Promise<ApiResponse<void>> =>
    api(`/admin/users/${id}/reset-password`, {
      method: 'PUT',
      body: { new_password: newPassword },
    }),
}
