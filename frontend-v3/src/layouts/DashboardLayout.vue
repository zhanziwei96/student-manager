<script setup lang="ts">
import { computed, type Component, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores'
import { ToastContainer, MobileDrawer, BottomNav } from '@/components/ui'
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
  BookMarked,
  Menu,
  MessageCircle,
  Search,
  CalendarRange,
  Layers,
  Library,
  Presentation,
  CalendarDays,
  Trophy,
} from 'lucide-vue-next'
import { KeyRound } from 'lucide-vue-next'
import { onClickOutside } from '@vueuse/core'
import { ChangePasswordDialog } from '@/components/ui'

const authStore = useAuthStore()
const route = useRoute()

const user = computed(() => authStore.user)
const isAdmin = computed(() => authStore.isAdmin)

const showMobileMenu = ref(false)
const showDropdown = ref(false)
const showChangePassword = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

interface NavItem {
  name: string
  path: string
  icon: Component
}

// 导航分组（管理员按管理域分组；教师/学生为单组平面列表）
const navGroups = computed(() => {
  const groups: { label: string; items: NavItem[] }[] = []

  if (authStore.isAdmin) {
    groups.push(
      {
        label: '核心管理',
        items: [
          { name: '仪表板', path: '/admin', icon: LayoutDashboard },
          { name: '学期管理', path: '/admin/semesters', icon: CalendarRange },
          { name: '届管理', path: '/admin/cohorts', icon: Layers },
          { name: '班级管理', path: '/admin/classes', icon: School },
          { name: '课程管理', path: '/admin/courses', icon: Library },
          { name: '教学班', path: '/admin/offerings', icon: Presentation }
        ]
      },
      {
        label: '人员管理',
        items: [
          { name: '学生管理', path: '/admin/students', icon: Users },
          { name: '教师管理', path: '/admin/teachers', icon: User }
        ]
      },
      {
        label: '教学运营',
        items: [
          { name: '课表管理', path: '/admin/schedules', icon: CalendarDays },
          { name: '科目管理', path: '/admin/subjects', icon: BookMarked },
          { name: '签到管理', path: '/admin/checkins', icon: CheckCircle }
        ]
      }
    )
  } else if (authStore.isTeacher) {
    groups.push({
      label: '',
      items: [
        { name: '仪表板', path: '/teacher', icon: LayoutDashboard },
        { name: '我的教学班', path: '/teacher/my-offerings', icon: Presentation },
        { name: '排行榜', path: '/teacher/rankings', icon: Trophy },
        { name: '课堂签到', path: '/teacher/session', icon: Calendar },
        { name: '课表管理', path: '/teacher/schedules', icon: BookOpen },
        { name: '科目管理', path: '/teacher/subjects', icon: BookMarked },
        { name: '合作项目', path: '/teacher/group-tasks', icon: Users },
        { name: '小组管理', path: '/teacher/groups', icon: GraduationCap },
        { name: '课堂问答', path: '/teacher/questions', icon: MessageCircle },
        { name: '失物招领', path: '/teacher/lost-found', icon: Search }
      ]
    })
  } else if (authStore.isStudent) {
    groups.push({
      label: '',
      items: [
        { name: '仪表板', path: '/student', icon: LayoutDashboard },
        { name: '我的成绩', path: '/student/grades', icon: GraduationCap },
        { name: '排行榜', path: '/student/rankings', icon: Trophy },
        { name: '课堂签到', path: '/student/checkin', icon: CheckCircle },
        { name: '我的小组', path: '/student/my-group', icon: Users },
        { name: '课堂问答', path: '/student/questions', icon: MessageCircle },
        { name: '失物招领', path: '/student/lost-found', icon: Search }
      ]
    })
  }

  return groups
})

const isActive = (path: string) => {
  if (path === '/admin' || path === '/teacher' || path === '/student') {
    return route.path === path
  }
  return route.path.startsWith(path)
}

const handleLogout = async () => {
  await authStore.logout()
}

// 点击外部关闭下拉菜单
onClickOutside(dropdownRef, () => {
  showDropdown.value = false
})

const handleChangePassword = () => {
  showDropdown.value = false
  showChangePassword.value = true
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

      <!-- User info - clickable dropdown -->
      <div ref="dropdownRef" class="relative border-b border-[#e5e5e5] p-4">
        <button
          class="flex w-full items-center gap-3 rounded-xl p-1 hover:bg-[#fafafa]"
          @click="showDropdown = !showDropdown"
        >
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-[#fafafa]">
            <User class="h-5 w-5 text-[#737373]" />
          </div>
          <div class="flex-1 min-w-0 text-left">
            <p class="truncate text-sm font-medium text-black">
              {{ user?.name }}
            </p>
            <p class="truncate text-xs text-[#a3a3a3] capitalize">
              {{ user?.role === 'admin' ? '管理员' : user?.role === 'teacher' ? '教师' : '学生' }}
            </p>
          </div>
        </button>

        <!-- Dropdown menu -->
        <div
          v-if="showDropdown"
          class="absolute left-4 right-4 top-full mt-1 rounded-xl border border-[#e5e5e5] bg-white py-1 z-10"
        >
          <button
            class="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-[#737373] hover:bg-[#fafafa] hover:text-black"
            @click="handleChangePassword"
          >
            <KeyRound class="h-4 w-4" />
            修改密码
          </button>
          <button
            class="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-[#737373] hover:bg-[#fafafa] hover:text-black"
            @click="handleLogout"
          >
            <LogOut class="h-4 w-4" />
            退出登录
          </button>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="space-y-4 p-4">
        <div
          v-for="group in navGroups"
          :key="group.label || 'main'"
          class="space-y-1"
        >
          <p
            v-if="group.label"
            class="px-3 pb-1 text-xs font-medium text-[#a3a3a3]"
          >
            {{ group.label }}
          </p>
          <RouterLink
            v-for="item in group.items"
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
        </div>
      </nav>

      <!-- Bottom spacer -->
      <div class="absolute bottom-0 left-0 right-0 p-4">
      </div>
    </aside>

    <!-- 移动端：抽屉菜单 -->
    <MobileDrawer v-model:open="showMobileMenu" @change-password="showChangePassword = true" />

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

    <!-- Change Password Dialog -->
    <ChangePasswordDialog v-model:open="showChangePassword" />
  </div>
</template>
