import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { authApi } from '@/api'
import type { User, LoginRequest } from '@/types'

/**
 * Auth Store using Pinia Setup Store + TanStack Query
 * Based on: https://github.com/vuejs/pinia
 */
export const useAuthStore = defineStore('auth', () => {
  const queryClient = useQueryClient()
  const user = ref<User | null>(null)

  // 计算属性 getters
  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isTeacher = computed(() => user.value?.role === 'teacher')
  const isStudent = computed(() => user.value?.role === 'student')

  // 获取当前用户查询
  const { refetch: fetchUserInfo } = useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      const res = await authApi.getMe()
      if (res.success && res.data) {
        user.value = res.data
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch user')
    },
    enabled: false, // Don't run automatically
    retry: false,
  })

  // 登录 mutation
  const loginMutation = useMutation({
    mutationFn: async (data: LoginRequest) => {
      const res = await authApi.login(data)
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Login failed')
    },
    onSuccess: () => {
      // 登录后获取完整用户信息
      fetchUserInfo()
    },
  })

  // 登出 mutation
  const logoutMutation = useMutation({
    mutationFn: async () => {
      const res = await authApi.logout()
      if (!res.success) {
        throw new Error(res.message || 'Logout failed')
      }
    },
    onSuccess: () => {
      // 清除用户状态
      user.value = null
      // 清除所有查询缓存
      queryClient.clear()
      // 通过刷新页面重置所有 store
      window.location.href = '/login'
    },
  })

  // 操作方法
  const login = async (data: LoginRequest) => {
    return loginMutation.mutateAsync(data)
  }

  const logout = async () => {
    return logoutMutation.mutateAsync()
  }

  return {
    // State
    user,
    // Getters
    isAuthenticated,
    isAdmin,
    isTeacher,
    isStudent,
    // Actions
    login,
    logout,
    fetchUserInfo,
    // Loading states
    isLoggingIn: computed(() => loginMutation.isPending.value),
    isLoggingOut: computed(() => logoutMutation.isPending.value),
    loginError: computed(() => loginMutation.error.value?.message),
  }
})
