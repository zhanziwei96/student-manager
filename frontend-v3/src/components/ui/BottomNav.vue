<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores'
import { LayoutDashboard, Users, CheckCircle, BookOpen } from 'lucide-vue-next'

const authStore = useAuthStore()
const route = useRoute()

const isTeacher = computed(() => authStore.isTeacher)
const isStudent = computed(() => authStore.isStudent)

// Teacher navigation items
const teacherItems = [
  { name: '仪表板', path: '/teacher', icon: LayoutDashboard },
  { name: '学生', path: '/teacher/students', icon: Users },
  { name: '签到', path: '/teacher/session', icon: CheckCircle },
  { name: '课表', path: '/teacher/schedules', icon: BookOpen }
]

// Student navigation items
const studentItems = [
  { name: '仪表板', path: '/student', icon: LayoutDashboard },
  { name: '签到', path: '/student/checkin', icon: CheckCircle }
]

const navItems = computed(() => {
  if (isTeacher.value) return teacherItems
  if (isStudent.value) return studentItems
  return []
})

const isActive = (path: string) => {
  return route.path === path
}
</script>

<template>
  <nav class="fixed bottom-0 left-0 right-0 z-40 bg-[#0a0a0f] border-t border-white/10 lg:hidden">
    <div class="flex items-center justify-around h-16">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        :class="[
          'flex flex-col items-center justify-center gap-1 flex-1 h-full min-w-0',
          isActive(item.path)
            ? 'text-primary'
            : 'text-white/50'
        ]"
      >
        <component :is="item.icon" class="h-6 w-6" />
        <span class="text-xs truncate max-w-full px-1">{{ item.name }}</span>
      </RouterLink>
    </div>
  </nav>
</template>
