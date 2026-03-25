import { defineStore } from 'pinia'
import { useAuthQuery } from '@/composables/useAuth'
import type { LoginRequest } from '@/types'

/**
 * Auth Store - Pinia 作为门面(facade)，实际状态由 TanStack Query 管理
 * 
 * FE-001 修复说明:
 * - 之前: Pinia 和 TanStack Query 同时管理 user 状态，手动同步，容易出错
 * - 现在: 服务端状态（用户数据）完全由 useAuthQuery (TanStack Query) 管理
 *        Pinia 只作为门面提供统一接口，保持向后兼容
 * 
 * 使用方式:
 * const authStore = useAuthStore()
 * authStore.login(credentials)
 * authStore.user // 响应式用户数据
 * 
 * 直接访问 Query (高级用法):
 * const { user, isAuthenticated } = useAuthQuery()
 */
export const useAuthStore = defineStore('auth', () => {
  // 使用 Query 管理服务端状态
  const authQuery = useAuthQuery()

  // 直接导出 Query 的状态和方法（保持接口一致）
  const user = authQuery.user
  const isAuthenticated = authQuery.isAuthenticated
  const isAdmin = authQuery.isAdmin
  const isTeacher = authQuery.isTeacher
  const isStudent = authQuery.isStudent
  const isLoggingIn = authQuery.isLoggingIn
  const isLoggingOut = authQuery.isLoggingOut
  const loginError = authQuery.loginError

  const login = async (data: LoginRequest) => {
    return authQuery.login(data)
  }

  const logout = async () => {
    return authQuery.logout()
  }

  const fetchUserInfo = async () => {
    return authQuery.fetchUserInfo()
  }

  return {
    // State
    user,
    isAuthenticated,
    isAdmin,
    isTeacher,
    isStudent,
    // Actions
    login,
    logout,
    fetchUserInfo,
    // Loading states
    isLoggingIn,
    isLoggingOut,
    loginError,
  }
})
