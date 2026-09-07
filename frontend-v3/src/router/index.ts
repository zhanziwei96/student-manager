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
      { path: 'subjects', name: 'AdminSubjects', component: () => import('@/views/teacher/Subjects.vue') },
      { path: 'group-tasks', name: 'AdminGroupTasks', component: () => import('@/views/teacher/GroupTasks.vue') },
      { path: 'group-tasks/:id/results', name: 'AdminGroupTaskResults', component: () => import('@/views/teacher/GroupTaskResults.vue') },
      { path: 'groups', name: 'AdminGroups', component: () => import('@/views/teacher/Groups.vue') },
      { path: 'lost-found', name: 'AdminLostFound', component: () => import('@/views/teacher/LostFound.vue') },
      { path: 'lost-found/create', name: 'AdminLostFoundCreate', component: () => import('@/views/teacher/LostFoundForm.vue') },
      { path: 'lost-found/:id', name: 'AdminLostFoundDetail', component: () => import('@/views/teacher/LostFoundDetail.vue') },
      { path: 'lost-found/:id/edit', name: 'AdminLostFoundEdit', component: () => import('@/views/teacher/LostFoundForm.vue') },
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
        component: () => import('@/views/teacher/CourseSession.vue'),
      },
      {
        path: 'schedules',
        name: 'TeacherSchedules',
        component: () => import('@/views/teacher/Schedules.vue'),
      },
      { path: 'subjects', name: 'TeacherSubjects', component: () => import('@/views/teacher/Subjects.vue') },
      {
        path: 'sessions-history',
        name: 'TeacherSessionsHistory',
        component: () => import('@/views/teacher/SessionsHistory.vue'),
      },
      { path: 'group-tasks', name: 'TeacherGroupTasks', component: () => import('@/views/teacher/GroupTasks.vue') },
      { path: 'group-tasks/:id/results', name: 'TeacherGroupTaskResults', component: () => import('@/views/teacher/GroupTaskResults.vue') },
      { path: 'group-tasks/:id/score', name: 'TeacherGroupTaskScore', component: () => import('@/views/teacher/GroupTaskScore.vue') },
      { path: 'groups', name: 'TeacherGroups', component: () => import('@/views/teacher/Groups.vue') },
      { path: 'questions', name: 'TeacherQuestions', component: () => import('@/views/teacher/TeacherQuestion.vue') },
      { path: 'lost-found', name: 'TeacherLostFound', component: () => import('@/views/teacher/LostFound.vue') },
      { path: 'lost-found/create', name: 'TeacherLostFoundCreate', component: () => import('@/views/teacher/LostFoundForm.vue') },
      { path: 'lost-found/:id', name: 'TeacherLostFoundDetail', component: () => import('@/views/teacher/LostFoundDetail.vue') },
      { path: 'lost-found/:id/edit', name: 'TeacherLostFoundEdit', component: () => import('@/views/teacher/LostFoundForm.vue') },
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
      { path: 'my-group', name: 'StudentMyGroup', component: () => import('@/views/student/MyGroup.vue') },
      { path: 'group-evaluations', name: 'StudentGroupEvaluations', component: () => import('@/views/student/GroupEvaluations.vue') },
      { path: 'group-results', name: 'StudentGroupResults', component: () => import('@/views/student/GroupResults.vue') },
      { path: 'questions', name: 'StudentQuestions', component: () => import('@/views/student/StudentQuestion.vue') },
      { path: 'lost-found', name: 'StudentLostFound', component: () => import('@/views/student/LostFound.vue') },
      { path: 'lost-found/:id', name: 'StudentLostFoundDetail', component: () => import('@/views/student/LostFoundDetail.vue') },
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
