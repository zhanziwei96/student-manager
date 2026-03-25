import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { authApi } from '@/api'
import type { LoginRequest } from '@/types'
import { computed } from 'vue'

/**
 * 认证状态管理 - FE-001 + FE-003 修复
 *
 * - FE-001: 使用 TanStack Query 管理服务端状态，避免与 Pinia 双重状态管理
 * - FE-003: 使用统一的 API 响应处理，无需手动检查 res.success
 */
export function useAuthQuery() {
  const queryClient = useQueryClient()

  // 当前用户查询 - 服务端状态由 Query 管理
  const {
    data: user,
    isPending: isLoadingUser,
    error: userError,
    refetch: fetchUserInfo
  } = useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      // FE-003: 直接获取数据，错误自动抛出
      return await authApi.getMe()
    },
    enabled: false,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

  // 计算属性派生状态
  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isTeacher = computed(() => user.value?.role === 'teacher')
  const isStudent = computed(() => user.value?.role === 'student')

  // 登录 mutation
  const loginMutation = useMutation({
    mutationFn: async (data: LoginRequest) => {
      // FE-003: 直接获取数据，错误自动抛出
      return await authApi.login(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] })
    },
  })

  // 登出 mutation
  const logoutMutation = useMutation({
    mutationFn: async () => {
      // FE-003: 直接调用，错误自动抛出
      await authApi.logout()
    },
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ['me'] })
      queryClient.clear()
      window.location.href = '/login'
    },
  })

  const login = async (data: LoginRequest) => {
    await loginMutation.mutateAsync(data)
    const { data: userInfo } = await fetchUserInfo()
    return userInfo
  }

  const logout = async () => {
    return logoutMutation.mutateAsync()
  }

  return {
    user,
    isLoadingUser,
    userError,
    isAuthenticated,
    isAdmin,
    isTeacher,
    isStudent,
    login,
    logout,
    fetchUserInfo,
    isLoggingIn: computed(() => loginMutation.isPending.value),
    isLoggingOut: computed(() => logoutMutation.isPending.value),
    loginError: computed(() => loginMutation.error.value?.message),
  }
}
