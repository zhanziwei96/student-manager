import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { getUserInfo } from '@/api'

export const useUserStore = defineStore('user', () => {
  // State - 不存储在 Cookie，仅内存
  const userInfo = ref(null)
  const isLoading = ref(false)

  // Getters
  const isLoggedIn = computed(() => !!userInfo.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')
  const isTeacher = computed(() => userInfo.value?.role === 'teacher')
  const isStudent = computed(() => userInfo.value?.role === 'student')
  const userId = computed(() => userInfo.value?.sub)
  const username = computed(() => userInfo.value?.username || '')
  const userName = computed(() => userInfo.value?.name || '')
  const role = computed(() => userInfo.value?.role || '')

  // Actions
  async function fetchUserInfo() {
    // 从后端获取用户信息
    try {
      isLoading.value = true
      const res = await getUserInfo()
      if (res.success && res.data) {
        userInfo.value = res.data
        return true
      }
      return false
    } catch (error) {
      userInfo.value = null
      return false
    } finally {
      isLoading.value = false
    }
  }

  function setUser(data) {
    // 登录成功后设置用户信息
    userInfo.value = data
  }

  function clearUser() {
    // 登出时清除用户信息
    userInfo.value = null
  }

  return {
    userInfo,
    isLoading,
    isLoggedIn,
    isAdmin,
    isTeacher,
    isStudent,
    userId,
    username,
    userName,
    role,
    fetchUserInfo,
    setUser,
    clearUser
  }
})
