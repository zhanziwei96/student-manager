import { api } from '@/lib/api'
import type {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  User,
  ChangePasswordRequest,
} from '@/types'

/**
 * 认证相关 API
 * 后端路由: /api/login, /api/logout, /api/me, /api/change-password
 */
export const authApi = {
  login: (data: LoginRequest): Promise<ApiResponse<LoginResponse>> =>
    api('/login', { method: 'POST', body: data }),

  logout: (): Promise<ApiResponse<void>> =>
    api('/logout', { method: 'POST' }),

  getMe: (): Promise<ApiResponse<User>> =>
    api('/me', { method: 'GET' }),

  changePassword: (data: ChangePasswordRequest): Promise<ApiResponse<void>> =>
    api('/change-password', { method: 'POST', body: data }),
}
