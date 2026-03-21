import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    name: 'PublicHome',
    component: () => import('@/views/PublicHome.vue')
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('@/views/Home.vue')
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
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 需要登录但未登录
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return next('/login')
  }
  
  // 已登录用户访问登录页，根据角色重定向
  if (to.meta.guest && userStore.isLoggedIn && userStore.role) {
    const roleRoutes = {
      admin: '/admin',
      teacher: '/teacher',
      student: '/student'
    }
    return next(roleRoutes[userStore.role] || '/')
  }
  
  // 角色权限检查
  if (to.meta.requiresAuth && to.meta.role) {
    if (userStore.role !== to.meta.role) {
      // 用户角色与路由不匹配，重定向到对应角色的首页
      const roleRoutes = {
        admin: '/admin',
        teacher: '/teacher',
        student: '/student'
      }
      return next(roleRoutes[userStore.role] || '/login')
    }
  }
  
  next()
})

export default router
