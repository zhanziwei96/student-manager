import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types'
import { UserRoleConst } from '@/types/api'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('@/views/LandingPage.vue'),
    meta: { public: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginPage.vue'),
    meta: { public: true, guestOnly: true },
  },
  {
    path: '/admin',
    component: () => import('@/layouts/DashboardLayout.vue'),
    meta: { role: UserRoleConst.ADMIN },  // FE-002: 使用常量
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
      },
      {
        path: 'students',
        name: 'AdminStudents',
        component: () => import('@/views/admin/Students.vue'),
      },
      {
        path: 'teachers',
        name: 'AdminTeachers',
        component: () => import('@/views/admin/Teachers.vue'),
      },
      {
        path: 'classes',
        name: 'AdminClasses',
        component: () => import('@/views/admin/Classes.vue'),
      },
      {
        path: 'checkins',
        name: 'AdminCheckins',
        component: () => import('@/views/admin/Checkins.vue'),
      },
      {
        path: 'schedules',
        name: 'AdminSchedules',
        component: () => import('@/views/teacher/Schedules.vue'),
      },
    ],
  },
  {
    path: '/teacher',
    component: () => import('@/layouts/DashboardLayout.vue'),
    meta: { role: UserRoleConst.TEACHER },  // FE-002: 使用常量
    children: [
      {
        path: '',
        name: 'TeacherDashboard',
        component: () => import('@/views/teacher/Dashboard.vue'),
      },
      {
        path: 'students',
        name: 'TeacherStudents',
        component: () => import('@/views/teacher/Students.vue'),
      },
      {
        path: 'session',
        name: 'TeacherSession',
        component: () => import('@/views/teacher/ClassSession.vue'),
      },
      {
        path: 'schedules',
        name: 'TeacherSchedules',
        component: () => import('@/views/teacher/Schedules.vue'),
      },
    ],
  },
  {
    path: '/student',
    component: () => import('@/layouts/DashboardLayout.vue'),
    meta: { role: UserRoleConst.STUDENT },  // FE-002: 使用常量
    children: [
      {
        path: '',
        name: 'StudentDashboard',
        component: () => import('@/views/student/Dashboard.vue'),
      },
      {
        path: 'checkin',
        name: 'StudentCheckin',
        component: () => import('@/views/student/Checkin.vue'),
      },
      {
        path: 'leaderboard',
        name: 'StudentLeaderboard',
        component: () => import('@/views/student/Leaderboard.vue'),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guards
/**
 * FE-002 修复说明:
 *
 * ⚠️ 安全警告 ⚠️
 * 前端路由权限控制仅作为用户体验优化，不能替代后端权限验证。
 *
 * 原因:
 * 1. 客户端代码可被绕过（禁用 JS、直接访问 API）
 * 2. 前端路由守卫无法阻止恶意请求
 *
 * 真实权限控制应在:
 * - 后端 API 层进行验证（已实现）
 * - 数据库访问控制（已实现）
 *
 * 此路由守卫的作用:
 * - 防止已登录用户看到无权限页面（体验优化）
 * - 根据角色自动跳转到对应首页（导航辅助）
 */
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // FE-001: 从 Pinia store 获取认证状态
  // 实际状态由 TanStack Query 管理，Pinia 作为门面转发
  // 这样组件和路由守卫可以使用统一的接口

  // Fetch user info if not loaded
  if (!authStore.user && !to.meta.public) {
    try {
      await authStore.fetchUserInfo()
    } catch {
      // Not authenticated - user will be redirected to login below
    }
  }

  // Public routes
  if (to.meta.public) {
    if (to.meta.guestOnly && authStore.isAuthenticated) {
      return next(getRedirectPath(authStore.user!.role))
    }
    return next()
  }

  // Protected routes
  if (!authStore.isAuthenticated) {
    return next('/login')
  }

  // Role check - 仅作为体验优化，真实权限验证在后端
  if (to.meta.role && authStore.user?.role !== to.meta.role) {
    return next(getRedirectPath(authStore.user!.role))
  }

  next()
})

function getRedirectPath(role: UserRole): string {
  const paths: Record<UserRole, string> = {
    admin: '/admin',
    teacher: '/teacher',
    student: '/student',
  }
  return paths[role] || '/'
}

export default router
