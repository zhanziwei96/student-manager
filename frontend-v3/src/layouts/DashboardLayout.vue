<script setup lang="ts">
import { computed, type Component, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores'
import { Button, ToastContainer, MobileDrawer, BottomNav } from '@/components/ui'
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  Calendar,
  LogOut,
  User,
  School,
  CheckCircle,
  BookOpen,
  Menu,
} from 'lucide-vue-next'

const authStore = useAuthStore()
const route = useRoute()

const user = computed(() => authStore.user)
const isAdmin = computed(() => authStore.isAdmin)

const showMobileMenu = ref(false)

// Navigation items based on role
const navItems = computed(() => {
  const items: { name: string; path: string; icon: Component }[] = []

  if (authStore.isAdmin) {
    items.push(
      { name: '仪表板', path: '/admin', icon: LayoutDashboard },
      { name: '学生管理', path: '/admin/students', icon: Users },
      { name: '教师管理', path: '/admin/teachers', icon: User },
      { name: '班级管理', path: '/admin/classes', icon: School },
      { name: '课表管理', path: '/admin/schedules', icon: BookOpen },
      { name: '签到管理', path: '/admin/checkins', icon: CheckCircle }
    )
  } else if (authStore.isTeacher) {
    items.push(
      { name: '仪表板', path: '/teacher', icon: LayoutDashboard },
      { name: '学生管理', path: '/teacher/students', icon: Users },
      { name: '课堂签到', path: '/teacher/session', icon: Calendar },
      { name: '课表管理', path: '/teacher/schedules', icon: BookOpen }
    )
  } else if (authStore.isStudent) {
    items.push(
      { name: '仪表板', path: '/student', icon: LayoutDashboard },
      { name: '课堂签到', path: '/student/checkin', icon: CheckCircle }
    )
  }

  return items
})

const isActive = (path: string) => {
  return route.path === path
}

const handleLogout = async () => {
  await authStore.logout()
}
</script>

<template>
  <div class="min-h-screen bg-[#fafafa]">
    <!-- 移动端：顶部导航栏 -->
    <header class="lg:hidden fixed top-0 left-0 right-0 h-14 z-40
                   bg-white border-b border-[#e5e5e5]
                   flex items-center justify-between px-4">
      <div class="flex items-center gap-2">
        <GraduationCap class="h-6 w-6 text-black" />
        <span class="text-lg font-medium text-black">智慧课堂</span>
      </div>
      <button
        class="p-2 -mr-2 rounded-lg text-[#a3a3a3] hover:text-black hover:bg-[#fafafa] min-h-[44px] min-w-[44px] flex items-center justify-center"
        @click="showMobileMenu = true"
      >
        <Menu class="h-6 w-6" />
      </button>
    </header>

    <!-- 桌面端：固定侧边栏 -->
    <aside class="hidden lg:block lg:fixed lg:left-0 lg:top-0 lg:z-40
                  lg:h-screen lg:w-64
                  border-r border-[#e5e5e5] bg-white">
      <!-- Logo -->
      <div class="flex h-16 items-center border-b border-[#e5e5e5] px-6">
        <GraduationCap class="h-8 w-8 text-black" />
        <span class="ml-3 text-xl font-medium text-black">智慧课堂</span>
      </div>

      <!-- User info -->
      <div class="border-b border-[#e5e5e5] p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-[#fafafa]">
            <User class="h-5 w-5 text-[#737373]" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="truncate text-sm font-medium text-black">
              {{ user?.name }}
            </p>
            <p class="truncate text-xs text-[#a3a3a3] capitalize">
              {{ user?.role === 'admin' ? '管理员' : user?.role === 'teacher' ? '教师' : '学生' }}
            </p>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="space-y-1 p-4">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex items-center gap-3 rounded-full px-3 py-2 text-sm font-medium',
            isActive(item.path)
              ? 'bg-[#e5e5e5] text-black'
              : 'text-[#737373] hover:bg-[#fafafa] hover:text-black',
          ]"
        >
          <component :is="item.icon" class="h-5 w-5" />
          {{ item.name }}
        </RouterLink>
      </nav>

      <!-- Bottom actions -->
      <div class="absolute bottom-0 left-0 right-0 border-t border-[#e5e5e5] p-4">
        <Button
          variant="ghost"
          class="w-full justify-start gap-2 text-[#a3a3a3] hover:text-black"
          @click="handleLogout"
        >
          <LogOut class="h-5 w-5" />
          退出登录
        </Button>
      </div>
    </aside>

    <!-- 移动端：抽屉菜单 -->
    <MobileDrawer v-model:open="showMobileMenu" />

    <!-- 移动端：底部导航栏（仅学生/教师） -->
    <BottomNav v-if="!isAdmin" class="lg:hidden" />

    <!-- 主内容区：响应式边距 -->
    <main class="min-h-screen p-4 pt-16 pb-20 lg:ml-64 lg:p-8 lg:pt-8 lg:pb-8">
      <div class="mx-auto max-w-7xl">
        <RouterView />
      </div>
    </main>

    <!-- Toast 通知容器 -->
    <ToastContainer />
  </div>
</template>
