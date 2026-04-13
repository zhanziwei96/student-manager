<script setup lang="ts">
/**
 * 学生签到网格组件
 *
 * 展示班级学生列表，显示签到状态，支持快速签到 - 卡片化设计
 */
import { computed } from 'vue'
import { Card, Input, Badge } from '@/components/ui'
import { GraduationCap, Search, CheckCircle, UserX, Clock } from 'lucide-vue-next'
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
  checkingStudentIds?: string[]
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

// 签到率
const checkinRate = computed(() => {
  if (props.students.length === 0) return 0
  return Math.round((stats.value.checkedIn / stats.value.total) * 100)
})

// 获取签到率颜色
const getRateColor = (rate: number): string => {
  if (rate >= 90) return 'text-green-400 bg-green-500/20 border-green-500/30'
  if (rate >= 70) return 'text-blue-400 bg-blue-500/20 border-blue-500/30'
  if (rate >= 50) return 'text-orange-400 bg-orange-500/20 border-orange-500/30'
  return 'text-red-400 bg-red-500/20 border-red-500/30'
}

// 检查学生是否正在签到
const isStudentCheckingIn = (studentId: string): boolean => {
  return props.checkingStudentIds?.includes(studentId) ?? false
}

// 处理快速签到
const handleQuickCheckIn = (student: Student) => {
  // DEBUG: 验证点击时传入的 student 是否正确
  console.log('[DEBUG] handleQuickCheckIn clicked:', { id: student.id, student_id: student.student_id, name: student.name, checkedIn: student.checkedIn })
  if (!student.checkedIn && !isStudentCheckingIn(student.student_id)) {
    emit('quickCheckIn', student.student_id)
  }
}

// 获取姓名首字母
const getInitials = (name: string): string => {
  return name.charAt(0).toUpperCase()
}

// 获取头像背景色（基于学生ID）
const getAvatarColor = (studentId: string): string => {
  const colors = [
    'bg-blue-500/30 text-blue-400',
    'bg-green-500/30 text-green-400',
    'bg-purple-500/30 text-purple-400',
    'bg-orange-500/30 text-orange-400',
    'bg-pink-500/30 text-pink-400',
    'bg-cyan-500/30 text-cyan-400',
  ]
  // 使用学生ID的字符码之和来确定颜色
  const sum = studentId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[sum % colors.length]
}
</script>

<template>
  <Card class="border-[#e5e5e5] bg-white overflow-hidden">
    <!-- 头部 - 卡片化设计 -->
    <div class="p-5 border-b border-[#e5e5e5] bg-[#f5f5f5]">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <!-- 标题和统计 -->
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/20">
            <GraduationCap class="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 class="font-medium text-black flex items-center gap-2">
              班级学生列表
              <Badge variant="secondary" class="text-xs bg-[#f5f5f5]">
                {{ stats.total }}人
              </Badge>
            </h3>
            <div class="flex items-center gap-3 mt-0.5">
              <span class="text-xs text-green-400 flex items-center gap-1">
                <CheckCircle class="h-3 w-3" />
                已签到 {{ stats.checkedIn }}
              </span>
              <span class="text-xs text-orange-400 flex items-center gap-1">
                <UserX class="h-3 w-3" />
                未签到 {{ stats.notCheckedIn }}
              </span>
            </div>
          </div>
        </div>

        <!-- 搜索和签到率 -->
        <div class="flex items-center gap-3">
          <!-- 签到率徽章 -->
          <Badge
            v-if="stats.total > 0"
            class="px-2.5 py-1 text-sm font-medium border"
            :class="getRateColor(checkinRate)"
          >
            {{ checkinRate }}% 签到率
          </Badge>

          <!-- 搜索框 -->
          <div class="relative w-52">
            <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a3a3a3]" />
            <Input
              v-model="search"
              placeholder="搜索学生姓名或学号..."
              class="pl-10 h-10 bg-[#f5f5f5] border-[#e5e5e5] focus:border-primary/50"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div
      v-if="loading"
      class="flex h-64 items-center justify-center"
    >
      <div class="flex flex-col items-center gap-3">
        <div class="h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <p class="text-sm text-[#a3a3a3]">加载学生数据...</p>
      </div>
    </div>

    <!-- 学生网格 - 卡片化设计 -->
    <div
      v-else-if="filteredStudents.length > 0"
      class="p-5"
    >
      <!-- 未签到学生区域 -->
      <div v-if="notCheckedInStudents.length > 0" class="mb-6">
        <div class="flex items-center gap-2 mb-3">
          <div class="flex h-6 w-6 items-center justify-center rounded-lg bg-orange-500/20">
            <UserX class="h-3.5 w-3.5 text-orange-400" />
          </div>
          <h4 class="text-sm font-medium text-orange-400">
            未签到 ({{ notCheckedInStudents.length }}人)
          </h4>
          <div class="flex-1 h-px bg-orange-500/20" />
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
          <div
            v-for="student in notCheckedInStudents"
            :key="student.student_id"
            class="group relative rounded-xl border border-orange-500/20 bg-white p-4 transition-all duration-200 cursor-pointer hover:border-orange-500/40"
            :class="{ 'opacity-60 cursor-not-allowed pointer-events-none': isStudentCheckingIn(student.student_id) }"
            @click="handleQuickCheckIn(student)"
          >
            <!-- Loading 遮罩 -->
            <div
              v-if="isStudentCheckingIn(student.student_id)"
              class="absolute inset-0 z-10 flex items-center justify-center rounded-xl bg-black/10"
            >
              <div class="h-5 w-5 animate-spin rounded-full border-2 border-orange-400 border-t-transparent" />
            </div>

            <!-- 状态指示器 -->
            <div class="absolute top-3 right-3 flex h-5 w-5 items-center justify-center rounded-full bg-orange-500/20 text-orange-400">
              <span class="text-xs font-medium">!</span>
            </div>

            <!-- 学生信息 -->
            <div class="flex flex-col items-center text-center">
              <!-- 头像 -->
              <div
                class="flex h-12 w-12 items-center justify-center rounded-full text-base font-medium mb-2"
                :class="getAvatarColor(student.student_id)"
              >
                {{ getInitials(student.name) }}
              </div>

              <!-- 姓名 -->
              <p class="text-sm font-medium text-black truncate w-full">
                {{ student.name }}
              </p>

              <!-- 学号 -->
              <p class="text-xs text-[#a3a3a3] mt-0.5 font-mono">
                {{ student.student_id }}
              </p>

              <!-- 点击提示 -->
              <div class="mt-2 flex items-center gap-1 text-xs text-orange-400/70 group-hover:text-orange-400 transition-colors">
                <CheckCircle class="h-3 w-3" />
                <span>点击签到</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 已签到学生区域 -->
      <div v-if="checkedInStudents.length > 0">
        <div class="flex items-center gap-2 mb-3">
          <div class="flex h-6 w-6 items-center justify-center rounded-lg bg-green-500/20">
            <CheckCircle class="h-3.5 w-3.5 text-green-400" />
          </div>
          <h4 class="text-sm font-medium text-green-400">
            已签到 ({{ checkedInStudents.length }}人)
          </h4>
          <div class="flex-1 h-px bg-green-500/20" />
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
          <div
            v-for="student in checkedInStudents"
            :key="student.student_id"
            class="relative rounded-xl border border-green-500/20 bg-white p-4 transition-all duration-200"
          >
            <!-- 状态指示器 -->
            <div class="absolute top-3 right-3 flex h-5 w-5 items-center justify-center rounded-full bg-green-500/20 text-green-400">
              <CheckCircle class="h-3 w-3" />
            </div>

            <!-- 学生信息 -->
            <div class="flex flex-col items-center text-center">
              <!-- 头像 -->
              <div
                class="flex h-12 w-12 items-center justify-center rounded-full text-base font-medium mb-2"
                :class="getAvatarColor(student.student_id)"
              >
                {{ getInitials(student.name) }}
              </div>

              <!-- 姓名 -->
              <p class="text-sm font-medium text-green-400 truncate w-full">
                {{ student.name }}
              </p>

              <!-- 学号 -->
              <p class="text-xs text-[#a3a3a3] mt-0.5 font-mono">
                {{ student.student_id }}
              </p>

              <!-- 签到时间 -->
              <div
                v-if="student.checkinTime"
                class="mt-2 flex items-center gap-1 text-xs text-[#a3a3a3]"
              >
                <Clock class="h-3 w-3" />
                <span>{{ formatTime(student.checkinTime) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div
      v-else
      class="flex h-64 flex-col items-center justify-center text-[#737373]"
    >
      <div class="flex h-16 w-16 items-center justify-center rounded-full bg-[#f5f5f5] mb-4">
        <GraduationCap class="h-8 w-8 opacity-50" />
      </div>
      <p class="text-lg font-medium">暂无学生数据</p>
      <p class="text-sm text-[#a3a3a3] mt-1">该班级暂时没有学生</p>
    </div>
  </Card>
</template>