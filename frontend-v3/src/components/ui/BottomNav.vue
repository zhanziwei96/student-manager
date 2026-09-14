<script setup lang="ts">
import { computed, ref, type Component } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores'
import BottomSheet from './BottomSheet.vue'
import {
  LayoutDashboard,
  Users,
  ScanLine,
  BookOpen,
  GraduationCap,
  Trophy,
  MessageCircle,
  Search,
  Presentation,
  CalendarDays,
  MoreHorizontal,
  KeyRound,
  LogOut
} from 'lucide-vue-next'

/**
 * BottomNav 移动端底部导航（iOS HIG：≤ 5 个 tab）
 *
 * - 签到为中央凸起主操作按钮（56px 黑色圆形）
 * - 其余低频入口收进「更多」BottomSheet
 * - 底部安全区 padding + 毛玻璃材质（不支持 backdrop-filter 时降级实色）
 *
 * 注：lucide 图标为描边风格（路径 fill="none"），选中态不设置 fill，
 * 否则会把图标填成色块。选中态用 黑色文字 + font-medium 区分。
 */

const emit = defineEmits<{
  changePassword: []
}>()

const authStore = useAuthStore()
const route = useRoute()

const isTeacher = computed(() => authStore.isTeacher)
const isStudent = computed(() => authStore.isStudent)

// 「更多」面板开关
const showMore = ref(false)

// 当前签到路由（中央主操作）
const checkinPath = computed(() => (isTeacher.value ? '/teacher/session' : '/student/checkin'))

// 导航条目：tab（普通）/ checkin（中央签到）/ more（更多按钮）
type BarItem =
  | { kind: 'tab'; name: string; path: string; icon: Component }
  | { kind: 'checkin' }
  | { kind: 'more' }

interface SheetItem {
  name: string
  path: string
  icon: Component
}

// 教师：仪表板 / 学生 / [签到] / 课表 / 更多
const teacherBar: BarItem[] = [
  { kind: 'tab', name: '仪表板', path: '/teacher', icon: LayoutDashboard },
  { kind: 'tab', name: '学生', path: '/teacher/students', icon: Users },
  { kind: 'checkin' },
  { kind: 'tab', name: '课表', path: '/teacher/schedules', icon: BookOpen },
  { kind: 'more' }
]

// 学生：仪表板 / 小组 / [签到] / 成绩 / 更多
const studentBar: BarItem[] = [
  { kind: 'tab', name: '仪表板', path: '/student', icon: LayoutDashboard },
  { kind: 'tab', name: '小组', path: '/student/my-group', icon: Users },
  { kind: 'checkin' },
  { kind: 'tab', name: '成绩', path: '/student/grades', icon: GraduationCap },
  { kind: 'more' }
]

// 「更多」面板内的低频入口
const teacherMore: SheetItem[] = [
  { name: '我的教学班', path: '/teacher/my-offerings', icon: Presentation },
  { name: '小组管理', path: '/teacher/groups', icon: GraduationCap },
  { name: '课堂问答', path: '/teacher/questions', icon: MessageCircle },
  { name: '排行榜', path: '/teacher/rankings', icon: Trophy },
  { name: '历史课堂', path: '/teacher/sessions-history', icon: CalendarDays },
  { name: '失物招领', path: '/teacher/lost-found', icon: Search }
]

const studentMore: SheetItem[] = [
  { name: '课堂问答', path: '/student/questions', icon: MessageCircle },
  { name: '排行榜', path: '/student/rankings', icon: Trophy },
  { name: '失物招领', path: '/student/lost-found', icon: Search }
]

const barItems = computed<BarItem[]>(() => {
  if (isTeacher.value) return teacherBar
  if (isStudent.value) return studentBar
  return []
})

const moreItems = computed<SheetItem[]>(() => {
  if (isTeacher.value) return teacherMore
  if (isStudent.value) return studentMore
  return []
})

// 与 DashboardLayout 一致：角色根路径精确匹配，其余前缀匹配。
// 前缀匹配带路径段边界：/teacher/session 不能命中 /teacher/sessions-history
const isActive = (path: string) => {
  if (path === '/teacher' || path === '/student') {
    return route.path === path
  }
  return route.path === path || route.path.startsWith(path + '/')
}

// 当前路由属于「更多」面板条目时，更多 tab 呈选中态
const moreActive = computed(() => moreItems.value.some((item) => isActive(item.path)))

const handleChangePassword = () => {
  showMore.value = false
  emit('changePassword')
}

const handleLogout = async () => {
  try {
    await authStore.logout()
  } finally {
    // 失败路径也要收起面板（路由 watcher 只覆盖成功跳转的情况）
    showMore.value = false
  }
}
</script>

<template>
  <nav class="bottom-nav-glass fixed bottom-0 left-0 right-0 z-40 border-t border-[#e5e5e5] lg:hidden">
    <div class="flex h-16 items-stretch">
      <template
        v-for="item in barItems"
        :key="item.kind === 'tab' ? item.path : item.kind"
      >
        <!-- 普通 tab -->
        <RouterLink
          v-if="item.kind === 'tab'"
          :to="item.path"
          class="flex h-full min-w-0 flex-1 flex-col items-center justify-center gap-1"
          :class="isActive(item.path) ? 'text-black font-medium' : 'text-[#525252]'"
        >
          <component :is="item.icon" class="h-6 w-6" />
          <span class="max-w-full truncate px-1 text-xs">{{ item.name }}</span>
        </RouterLink>

        <!-- 中央签到主操作：56px 凸起黑色圆形按钮 -->
        <div
          v-else-if="item.kind === 'checkin'"
          class="flex flex-1 items-center justify-center"
        >
          <RouterLink
            :to="checkinPath"
            aria-label="签到"
            class="-mt-6 flex h-14 w-14 items-center justify-center rounded-full bg-black text-white shadow-lg"
            :class="isActive(checkinPath) ? 'ring-2 ring-black/20' : ''"
          >
            <ScanLine class="h-6 w-6" />
          </RouterLink>
        </div>

        <!-- 更多：打开 BottomSheet -->
        <button
          v-else
          type="button"
          aria-haspopup="dialog"
          :aria-expanded="showMore"
          class="flex h-full min-w-0 flex-1 flex-col items-center justify-center gap-1"
          :class="moreActive ? 'text-black font-medium' : 'text-[#525252]'"
          @click="showMore = true"
        >
          <MoreHorizontal class="h-6 w-6" />
          <span class="text-xs">更多</span>
        </button>
      </template>
    </div>

    <!-- 更多面板：低频入口 + 账号操作 -->
    <BottomSheet v-model:open="showMore" title="更多">
      <nav class="flex flex-col pb-2">
        <RouterLink
          v-for="item in moreItems"
          :key="item.path"
          :to="item.path"
          class="flex min-h-12 items-center gap-3 rounded-xl px-3 text-sm text-black hover:bg-[#fafafa]"
          @click="showMore = false"
        >
          <component :is="item.icon" class="h-5 w-5 text-[#525252]" />
          {{ item.name }}
        </RouterLink>

        <div class="my-2 border-t border-[#e5e5e5]" />

        <button
          type="button"
          class="flex min-h-12 items-center gap-3 rounded-xl px-3 text-sm text-black hover:bg-[#fafafa]"
          @click="handleChangePassword"
        >
          <KeyRound class="h-5 w-5 text-[#525252]" />
          修改密码
        </button>
        <button
          type="button"
          class="flex min-h-12 items-center gap-3 rounded-xl px-3 text-sm text-black hover:bg-[#fafafa]"
          @click="handleLogout"
        >
          <LogOut class="h-5 w-5 text-[#525252]" />
          退出登录
        </button>
      </nav>
    </BottomSheet>
  </nav>
</template>

<style scoped>
/* 微信 WebView 兼容：不支持 backdrop-filter 时保持纯白底（同 BottomSheet） */
.bottom-nav-glass {
  background: #ffffff;
  /* 刘海屏底部安全区（--safe-bottom） */
  padding-bottom: var(--safe-bottom);
}

@supports (backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px)) {
  .bottom-nav-glass {
    background: var(--color-surface-glass);
    backdrop-filter: var(--material-blur);
    -webkit-backdrop-filter: var(--material-blur);
  }
}
</style>
