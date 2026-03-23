import { api } from '@/lib/api'
import type {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  User,
  ChangePasswordRequest,
} from '@/types'

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
