import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    name: 'PublicHome',
    component: () => import('@/views/PublicHome.vue')
  },
  {
    path: '/stats',
    name: 'Stats',
    component: () => import('@/views/Stats.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/Admin.vue'),
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/teacher',
    name: 'Teacher',
    component: () => import('@/views/Teacher.vue'),
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/student',
    name: 'Student',
    component: () => import('@/views/Student.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/checkin',
    name: 'Checkin',
    component: () => import('@/views/Checkin.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 如果路由需要认证
  if (to.meta.requiresAuth) {
    // 初始化用户信息（如果未加载且未在加载中）
    if (!userStore.userInfo && !userStore.isLoading) {
      await userStore.fetchUserInfo()
    }
    
    // 需要登录但未登录
    if (!userStore.isLoggedIn) {
      return next('/login')
    }
    
    // 角色权限检查
    if (to.meta.role && userStore.role !== to.meta.role) {
      const roleRoutes = {
        admin: '/admin',
        teacher: '/teacher',
        student: '/student'
      }
      return next(roleRoutes[userStore.role] || '/login')
    }
  }
  
  // 已登录用户访问登录页，根据角色重定向
  if (to.meta.guest && userStore.isLoggedIn) {
    const roleRoutes = {
      admin: '/admin',
      teacher: '/teacher',
      student: '/student'
    }
    return next(roleRoutes[userStore.role] || '/')
  }
  
  // 公开路由直接放行
  next()
})

export default router
