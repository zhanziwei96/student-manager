import { get, post } from '@/lib/api'
import type {
  LoginRequest,
  LoginResponse,
  User,
  ChangePasswordRequest,
} from '@/types'

/**
 * 认证相关 API - FE-003 修复后
 *
 * 调用方无需再检查 res.success，错误会自动抛出
 * 返回类型直接是数据 T，而不是 ApiResponse<T>
 */
export const authApi = {
  login: (data: LoginRequest): Promise<LoginResponse> =>
    post('/login', data),

  logout: (): Promise<void> =>
    post('/logout'),

  getMe: (): Promise<User> =>
    get('/me'),

  changePassword: (data: ChangePasswordRequest): Promise<void> =>
    post('/change-password', data),
}
