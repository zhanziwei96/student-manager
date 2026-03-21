import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import Cookies from 'js-cookie'

const COOKIE_OPTIONS = { path: '/', sameSite: 'strict' }

export const useUserStore = defineStore('user', () => {
  // State - 从 Cookie 初始化
  const userId = ref(Cookies.get('user_id') || null)
  const username = ref(Cookies.get('username') || '')
  const userName = ref(Cookies.get('name') || '')
  const role = ref(Cookies.get('role') || '')

  // Getters
  const isLoggedIn = computed(() => !!userId.value)
  const isAdmin = computed(() => role.value === 'admin')
  const isTeacher = computed(() => role.value === 'teacher')
  const isStudent = computed(() => role.value === 'student')

  // Actions
  function setUser(id, name, displayName, userRole = '') {
    userId.value = id
    username.value = name
    userName.value = displayName || name
    role.value = userRole
    
    // 同步到 Cookie
    Cookies.set('user_id', id, COOKIE_OPTIONS)
    Cookies.set('username', name, COOKIE_OPTIONS)
    Cookies.set('name', displayName || name, COOKIE_OPTIONS)
    Cookies.set('role', userRole, COOKIE_OPTIONS)
  }

  function clearUser() {
    userId.value = null
    username.value = ''
    userName.value = ''
    role.value = ''
    
    // 清除 Cookie
    Cookies.remove('user_id', { path: '/' })
    Cookies.remove('username', { path: '/' })
    Cookies.remove('name', { path: '/' })
    Cookies.remove('role', { path: '/' })
  }

  return {
    userId,
    username,
    userName,
    role,
    isLoggedIn,
    isAdmin,
    isTeacher,
    isStudent,
    setUser,
    clearUser
  }
})
