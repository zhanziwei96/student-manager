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
    meta: { requiresAuth: true }
  },
  {
    path: '/teacher',
    name: 'Teacher',
    component: () => import('@/views/Teacher.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/student',
    name: 'Student',
    component: () => import('@/views/Student.vue'),
    meta: { requiresAuth: true }
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
  
  // 已登录用户访问登录页
  if (to.meta.guest && userStore.isLoggedIn) {
    return next('/admin')
  }
  
  next()
})

export default router
