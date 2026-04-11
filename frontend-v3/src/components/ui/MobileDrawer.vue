<script setup lang="ts">
import { X, User, LayoutDashboard, Users, GraduationCap, BookOpen, CheckCircle, School, KeyRound } from 'lucide-vue-next'
import { Button } from '.'
import { useAuthStore } from '@/stores'
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'changePassword': []
}>()

const authStore = useAuthStore()
const route = useRoute()

const user = computed(() => authStore.user)
const isAdmin = computed(() => authStore.isAdmin)
const isTeacher = computed(() => authStore.isTeacher)
const isStudent = computed(() => authStore.isStudent)

// Navigation items based on role
const navItems = computed(() => {
  const items: { name: string; path: string; icon: typeof User }[] = []

  if (isAdmin.value) {
    items.push(
      { name: '仪表板', path: '/admin', icon: LayoutDashboard },
      { name: '学生管理', path: '/admin/students', icon: Users },
      { name: '教师管理', path: '/admin/teachers', icon: User },
      { name: '班级管理', path: '/admin/classes', icon: School },
      { name: '课表管理', path: '/admin/schedules', icon: BookOpen },
      { name: '签到管理', path: '/admin/checkins', icon: CheckCircle }
    )
  } else if (isTeacher.value) {
    items.push(
      { name: '仪表板', path: '/teacher', icon: LayoutDashboard },
      { name: '学生管理', path: '/teacher/students', icon: Users },
      { name: '课堂签到', path: '/teacher/session', icon: CheckCircle },
      { name: '课表管理', path: '/teacher/schedules', icon: BookOpen },
      { name: '合作项目', path: '/teacher/group-tasks', icon: Users },
      { name: '小组管理', path: '/teacher/groups', icon: GraduationCap }
    )
  } else if (isStudent.value) {
    items.push(
      { name: '仪表板', path: '/student', icon: LayoutDashboard },
      { name: '课堂签到', path: '/student/checkin', icon: CheckCircle },
      { name: '我的小组', path: '/student/my-group', icon: Users },
      { name: '组间互评', path: '/student/group-evaluations', icon: CheckCircle },
      { name: '成绩单', path: '/student/group-results', icon: GraduationCap }
    )
  }

  return items
})

const isActive = (path: string) => {
  return route.path === path
}

const handleClose = () => {
  emit('update:open', false)
}

const handleLogout = async () => {
  await authStore.logout()
  handleClose()
}

const handleChangePassword = () => {
  emit('changePassword')
  handleClose()
}

// Close drawer on route change
watch(() => route.path, () => {
  handleClose()
})
</script>

<template>
  <!-- Overlay -->
  <Transition
    enter-active-class="transition-opacity duration-300"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity duration-200"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="open"
      class="fixed inset-0 z-50 bg-black/30 lg:hidden"
      @click="handleClose"
    />
  </Transition>

  <!-- Drawer -->
  <Transition
    enter-active-class="transition-transform duration-300 ease-out"
    enter-from-class="-translate-x-full"
    enter-to-class="translate-x-0"
    leave-active-class="transition-transform duration-200 ease-in"
    leave-from-class="translate-x-0"
    leave-to-class="-translate-x-full"
  >
    <aside
      v-if="open"
      class="fixed left-0 top-0 z-50 h-screen w-[280px] bg-white border-r border-[#e5e5e5] lg:hidden"
    >
      <!-- Header -->
      <div class="flex items-center justify-between h-16 px-4 border-b border-[#e5e5e5]">
        <div class="flex items-center gap-2">
          <GraduationCap class="h-6 w-6 text-black" />
          <span class="text-lg font-medium text-black">智慧课堂</span>
        </div>
        <button
          class="p-2 -mr-2 rounded-lg text-[#a3a3a3] hover:text-black hover:bg-[#fafafa]"
          @click="handleClose"
        >
          <X class="h-6 w-6" />
        </button>
      </div>

      <!-- User info -->
      <div class="p-4 border-b border-[#e5e5e5]">
        <div class="flex items-center gap-3">
          <div class="flex h-12 w-12 items-center justify-center rounded-full bg-[#fafafa]">
            <User class="h-6 w-6 text-[#737373]" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-base font-medium text-black truncate">
              {{ user?.name }}
            </p>
            <p class="text-sm text-[#a3a3a3]">
              {{ user?.role === 'admin' ? '管理员' : user?.role === 'teacher' ? '教师' : '学生' }}
            </p>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="p-2 space-y-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex items-center gap-4 rounded-full px-4 py-3.5 text-base font-medium',
            isActive(item.path)
              ? 'bg-[#e5e5e5] text-black'
              : 'text-[#737373] hover:bg-[#fafafa] hover:text-black'
          ]"
        >
          <component :is="item.icon" class="h-6 w-6" />
          {{ item.name }}
        </RouterLink>
      </nav>

      <!-- Change password -->
      <div class="px-2 pt-2 border-t border-[#e5e5e5] mx-2">
        <button
          class="flex w-full items-center gap-4 rounded-full px-4 py-3.5 text-base font-medium text-[#737373] hover:bg-[#fafafa] hover:text-black"
          @click="handleChangePassword"
        >
          <KeyRound class="h-6 w-6" />
          修改密码
        </button>
      </div>

      <!-- Bottom actions -->
      <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-[#e5e5e5]">
        <Button
          variant="ghost"
          class="w-full justify-start gap-3 text-[#a3a3a3] hover:text-black h-12"
          @click="handleLogout"
        >
          <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          退出登录
        </Button>
      </div>
    </aside>
  </Transition>
</template>
