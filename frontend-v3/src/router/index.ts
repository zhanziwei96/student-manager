import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types'

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
    meta: { role: 'admin' as UserRole },
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
    ],
  },
  {
    path: '/teacher',
    component: () => import('@/layouts/DashboardLayout.vue'),
    meta: { role: 'teacher' as UserRole },
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
    ],
  },
  {
    path: '/student',
    component: () => import('@/layouts/DashboardLayout.vue'),
    meta: { role: 'student' as UserRole },
    children: [
      {
        path: '',
        name: 'StudentDashboard',
        component: () => import('@/views/student/Dashboard.vue'),
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
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // Fetch user info if not loaded
  if (!authStore.user && !to.meta.public) {
    try {
      await authStore.fetchUserInfo()
    } catch (error) {
      // Not authenticated - user will be redirected to login below
      console.log('User not authenticated, redirecting to login')
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

  // Role check
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
