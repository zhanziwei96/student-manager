<script setup lang="ts">
/**
 * 学生签到网格组件
 *
 * 展示班级学生列表，显示签到状态，支持快速签到
 */
import { computed } from 'vue'
import { Card, Input } from '@/components/ui'
import { GraduationCap, Search, CheckCircle } from 'lucide-vue-next'
import { formatTime } from '@/lib/date'

interface Student {
  id: string
  student_id: string
  name: string
  checkedIn: boolean
  checkinTime?: string
}

const props = defineProps<{
  students: Student[]
  loading?: boolean
  searchQuery?: string
}>()

const emit = defineEmits<{
  'update:searchQuery': [query: string]
  'quickCheckIn': [studentId: string]
}>()

// 搜索关键词
const search = computed({
  get: () => props.searchQuery ?? '',
  set: (val) => emit('update:searchQuery', val)
})

// 过滤后的学生列表
const filteredStudents = computed(() => {
  if (!search.value.trim()) return props.students

  const query = search.value.toLowerCase()
  return props.students.filter(s =>
    s.name.toLowerCase().includes(query) ||
    s.student_id.toLowerCase().includes(query)
  )
})

// 按签到状态分组
const notCheckedInStudents = computed(() =>
  filteredStudents.value.filter(s => !s.checkedIn)
)

const checkedInStudents = computed(() =>
  filteredStudents.value.filter(s => s.checkedIn)
)

// 统计
const stats = computed(() => ({
  total: props.students.length,
  checkedIn: props.students.filter(s => s.checkedIn).length,
  notCheckedIn: props.students.filter(s => !s.checkedIn).length
}))

// 处理快速签到
const handleQuickCheckIn = (student: Student) => {
  if (!student.checkedIn) {
    emit('quickCheckIn', student.student_id)
  }
}
</script>

<template>
  <Card class="border-white/10 bg-white/[0.02]">
    <!-- 头部 -->
    <div class="p-4 border-b border-white/10 flex items-center justify-between">
      <div>
        <h3 class="font-medium text-white flex items-center gap-2">
          <GraduationCap class="h-5 w-5" />
          班级学生列表
          <span class="text-sm text-white/50">({{ stats.total }}人)</span>
        </h3>
      </div>
      <div class="relative w-48">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
        <Input
          v-model="search"
          placeholder="搜索学生..."
          class="pl-10 h-9"
        />
      </div>
    </div>

    <!-- 加载状态 -->
    <div
      v-if="loading"
      class="flex h-48 items-center justify-center"
    >
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>

    <!-- 学生网格 -->
    <div
      v-else-if="filteredStudents.length > 0"
      class="p-4"
    >
      <!-- 统计标签 -->
      <div class="flex items-center gap-4 mb-4">
        <div class="flex items-center gap-2">
          <div class="flex h-2 w-2 rounded-full bg-green-400" />
          <span class="text-sm text-white/60">已签到 {{ checkedInStudents.length }}人</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="flex h-2 w-2 rounded-full bg-red-400" />
          <span class="text-sm text-white/60">未签到 {{ notCheckedInStudents.length }}人</span>
        </div>
      </div>

      <!-- 学生卡片网格 -->
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        <div
          v-for="student in filteredStudents"
          :key="student.id"
          class="relative rounded-lg border p-3 transition-all cursor-pointer group"
          :class="[
            student.checkedIn
              ? 'bg-green-500/10 border-green-500/30 hover:border-green-500/50'
              : 'bg-red-500/10 border-red-500/30 hover:border-red-500/50 hover:bg-red-500/15'
          ]"
          @click="handleQuickCheckIn(student)"
        >
          <!-- 签到状态图标 -->
          <div
            class="absolute top-2 right-2 flex h-5 w-5 items-center justify-center rounded-full"
            :class="student.checkedIn ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'"
          >
            <CheckCircle
              v-if="student.checkedIn"
              class="h-3 w-3"
            />
            <span
              v-else
              class="text-xs"
            >!</span>
          </div>

          <!-- 学生信息 -->
          <div class="flex flex-col items-center text-center">
            <div
              class="flex h-10 w-10 items-center justify-center rounded-full text-sm font-medium mb-2"
              :class="student.checkedIn
                ? 'bg-green-500/20 text-green-400'
                : 'bg-red-500/20 text-red-400 group-hover:bg-red-500/30'"
            >
              {{ student.name.charAt(0) }}
            </div>
            <p
              class="text-sm font-medium truncate w-full"
              :class="student.checkedIn ? 'text-green-400' : 'text-red-400'"
            >
              {{ student.name }}
            </p>
            <p class="text-xs text-white/40 mt-0.5">
              {{ student.student_id }}
            </p>
            <p
              v-if="student.checkedIn && student.checkinTime"
              class="text-xs text-white/50 mt-1"
            >
              {{ formatTime(student.checkinTime) }}
            </p>
            <p
              v-else-if="!student.checkedIn"
              class="text-xs text-red-400/70 mt-1"
            >
              点击签到
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div
      v-else
      class="flex h-48 flex-col items-center justify-center text-white/60"
    >
      <GraduationCap class="mb-4 h-12 w-12 opacity-50" />
      <p>暂无学生数据</p>
    </div>
  </Card>
</template>