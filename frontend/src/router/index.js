import { createRouter, createWebHistory } from 'vue-router'
import Cookies from 'js-cookie'

const routes = [
  {
    path: '/',
    name: 'PublicHome',
    component: () => import('../views/PublicHome.vue')
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/Admin.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/checkin',
    name: 'Checkin',
    component: () => import('../views/Checkin.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/checkin-cards',
    name: 'CardCheckin',
    component: () => import('../views/CardCheckin.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userId = Cookies.get('user_id')
  
  if (to.meta.requiresAuth && !userId) {
    next('/login')
  } else {
    next()
  }
})

export default router
