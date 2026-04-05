<script setup lang="ts">
/**
 * 课堂签到页面 - 重构版
 *
 * 拆分后职责：
 * - 课堂会话管理（开始/结束）
 * - 协调子组件
 * - 处理业务逻辑和API调用
 *
 * 已拆分功能：
 * - StudentCheckinGrid.vue - 学生列表
 * - CheckinStats.vue - 统计卡片
 */
import { ref, computed } from 'vue'
import {
  useClassSession,
  useClassSessionStart,
  useClassSessionEnd,
  useStudentCheckIn,
  useActiveClassSessions,
  useToast
} from '@/composables'
import { useClasses, useClassStudents } from '@/composables/useClasses'
import { useSchedules } from '@/composables/useSchedules'
import { useTodayCheckins } from '@/composables/useCheckins'
import { useAuthStore } from '@/stores'
import { Card, Button, Input, Select } from '@/components/ui'
import {
  Play, Square, CheckCircle, Clock,
  AlertTriangle
} from 'lucide-vue-next'
import { getErrorMessage } from '@/lib/error'

// 子组件
import StudentCheckinGrid from '@/components/teacher/StudentCheckinGrid.vue'
import CheckinStats from '@/components/teacher/CheckinStats.vue'

// ===== 状态定义 =====
const className = ref('')
const courseName = ref('')
const studentCode = ref('')
const searchQuery = ref('')

// ===== 获取数据 =====
const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)

const { data: activeSession } = useClassSession()
const { mutateAsync: startSession, isPending: isStartingSession } = useClassSessionStart()
const { mutateAsync: endSession, isPending: isEndingSession } = useClassSessionEnd()
const { mutateAsync: checkIn, isPending: isCheckingIn } = useStudentCheckIn(
  computed(() => activeSession.value?.class_name || '')
)

const { data: activeSessions } = useActiveClassSessions()
const { data: classList } = useClasses()
const { data: schedules } = useSchedules()
const { data: classStudents, isPending: isLoadingStudents } = useClassStudents(
  computed(() => activeSession.value?.class_name || '')
)
const { data: todayCheckins, refetch: refetchCheckins } = useTodayCheckins(
  computed(() => activeSession.value?.class_name || '')
)

const { success: showSuccessToast, error: showErrorToast } = useToast()

// ===== 计算属性 =====
const isSessionActive = computed(() => !!activeSession.value)

// 其他教师占用的班级
const otherOccupiedClasses = computed(() => {
  if (!activeSessions.value) return []
  const currentUserId = currentUser.value?.id
  return activeSessions.value.filter(s => s.teacher_id !== currentUserId)
})

// 课程选项
const courseOptions = computed(() => {
  if (!schedules.value) return []
  const courseNames = new Set(schedules.value.map(s => s.course_name).filter(Boolean))
  return Array.from(courseNames).map(name => ({ value: name, label: name }))
})

// 班级选项
const availableClassOptions = computed(() => {
  if (!classList.value) return []
  const occupiedMap = new Map(
    activeSessions.value?.map(s => [s.class_name, s.teacher_name]) || []
  )

  return classList.value.map(cls => {
    const teacherName = occupiedMap.get(cls.name)
    return {
      value: cls.name,
      label: teacherName ? `${cls.name} (已被 ${teacherName} 老师占用)` : cls.name,
      disabled: !!teacherName
    }
  })
})

// 已签到学生ID集合
const checkedInStudentIds = computed(() => {
  if (!todayCheckins.value) return new Set()
  return new Set(todayCheckins.value.map(c => c.student_id))
})

// 学生列表（带签到状态）
const studentListWithCheckin = computed(() => {
  if (!classStudents.value) return []

  const checkinTimeMap = new Map<string, string>()
  todayCheckins.value?.forEach(c => {
    checkinTimeMap.set(c.student_id, c.checkin_time)
  })

  return classStudents.value.map(s => ({
    id: String(s.id),
    student_id: s.student_id,
    name: s.name,
    checkedIn: checkedInStudentIds.value.has(s.student_id),
    checkinTime: checkinTimeMap.get(s.student_id)
  }))
})

// 统计
const checkinStats = computed(() => {
  const total = classStudents.value?.length ?? 0
  const checkedIn = studentListWithCheckin.value.filter(s => s.checkedIn).length
  return { total, checkedIn, notCheckedIn: total - checkedIn }
})

// ===== 事件处理 =====
const handleStartSession = async () => {
  if (!className.value) {
    showErrorToast('请选择班级')
    return
  }

  try {
    await startSession({
      className: className.value,
      courseName: courseName.value || undefined
    })
    showSuccessToast('课堂已开始！')
    className.value = ''
    courseName.value = ''
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '开始课堂失败')
  }
}

const handleEndSession = async () => {
  try {
    await endSession()
    showSuccessToast('课堂已结束！')
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '结束课堂失败')
  }
}

const handleCheckIn = async () => {
  if (!studentCode.value.trim()) {
    showErrorToast('请输入学生代码')
    return
  }

  try {
    await checkIn(studentCode.value.trim())
    showSuccessToast('学生签到成功！')
    studentCode.value = ''
    refetchCheckins()
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '签到失败')
  }
}

const handleQuickCheckIn = async (studentId: string) => {
  try {
    await checkIn(studentId)
    showSuccessToast('签到成功！')
    refetchCheckins()
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '签到失败')
  }
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-5">
      <h1 class="text-2xl font-bold text-white">
        课堂签到
      </h1>
      <p class="text-white/60">
        管理您的活跃课堂
      </p>
    </div>

    <!-- Session status -->
    <Card
      class="border-white/10 p-4 md:p-6 mb-5"
      :class="isSessionActive ? 'bg-green-500/5 border-green-500/20' : 'bg-white/[0.02]'"
    >
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="flex items-center gap-3 md:gap-4">
          <div
            class="flex h-10 w-10 md:h-12 md:w-12 items-center justify-center rounded-full flex-shrink-0"
            :class="isSessionActive ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/60'"
          >
            <Clock class="h-5 w-5 md:h-6 md:w-6" />
          </div>
          <div class="min-w-0 flex-1">
            <h2 class="font-medium text-white">
              {{ isSessionActive ? '课堂进行中' : '暂无活跃课堂' }}
            </h2>
            <p
              v-if="activeSession"
              class="text-sm text-white/60 truncate"
            >
              {{ activeSession.class_name }} • 开始于 {{ activeSession.start_time }}
            </p>
            <p
              v-else-if="!isSessionActive"
              class="text-sm text-white/60"
            >
              选择班级开始新课堂
            </p>
          </div>
        </div>
        <div class="flex-shrink-0">
          <Button
            v-if="!isSessionActive"
            :loading="isStartingSession"
            class="w-full sm:w-auto min-h-[44px]"
            @click="handleStartSession"
          >
            <Play class="mr-2 h-4 w-4" />
            开始课堂
          </Button>
          <Button
            v-else
            variant="destructive"
            :loading="isEndingSession"
            class="w-full sm:w-auto min-h-[44px]"
            @click="handleEndSession"
          >
            <Square class="mr-2 h-4 w-4" />
            结束课堂
          </Button>
        </div>
      </div>
    </Card>

    <!-- Start session form -->
    <Card
      v-if="!isSessionActive"
      class="p-4 md:p-6 mb-5"
    >
      <h3 class="font-medium text-white text-base md:text-lg">
        开始新课堂
      </h3>
      <p class="text-sm text-white/60">
        选择课程和班级开始上课
      </p>

      <!-- 班级占用状态 -->
      <div
        v-if="otherOccupiedClasses.length > 0"
        class="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg"
      >
        <p class="text-sm text-yellow-400 flex items-center gap-2">
          <AlertTriangle class="h-4 w-4 flex-shrink-0" />
          以下班级正在被其他教师上课：
        </p>
        <ul class="mt-2 text-sm text-white/70 space-y-1">
          <li
            v-for="cls in otherOccupiedClasses"
            :key="cls.class_name"
          >
            {{ cls.class_name }} - {{ cls.teacher_name || '其他教师' }} 老师
          </li>
        </ul>
      </div>

      <div class="mt-4">
        <div class="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-4">
          <Select
            v-model="courseName"
            class="w-full"
            placeholder="请选择课程（可选）"
            :options="courseOptions"
          />
          <Select
            v-model="className"
            class="w-full"
            placeholder="请选择班级"
            :options="availableClassOptions"
          />
        </div>
        <Button
          :loading="isStartingSession"
          :disabled="!className"
          class="w-full min-h-[48px] md:min-h-[44px] text-base md:text-sm"
          @click="handleStartSession"
        >
          <Play class="mr-2 h-5 w-5 md:h-4 md:w-4" />
          开始上课
        </Button>
      </div>
    </Card>

    <!-- Active session content -->
    <template v-if="isSessionActive">
      <!-- Check-in form -->
      <Card class="p-4 md:p-6 mb-5">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20 flex-shrink-0">
            <CheckCircle class="h-5 w-5 text-primary" />
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="font-medium text-white">
              学生签到
            </h3>
            <p class="text-sm text-white/60">
              输入学生学号进行签到
            </p>
          </div>
        </div>
        <div class="mt-4 flex flex-col sm:flex-row gap-3 sm:gap-4">
          <Input
            v-model="studentCode"
            placeholder="请输入学生学号"
            class="w-full"
            @keyup.enter="handleCheckIn"
          />
          <Button
            :loading="isCheckingIn"
            class="w-full sm:w-auto min-h-[48px] md:min-h-[44px] flex-shrink-0"
            @click="handleCheckIn"
          >
            <CheckCircle class="mr-2 h-5 w-5 md:h-4 md:w-4" />
            签到
          </Button>
        </div>
      </Card>

      <!-- Stats -->
      <CheckinStats
        :stats="checkinStats"
        class="mb-5"
      />

      <!-- Student list -->
      <StudentCheckinGrid
        v-model:search-query="searchQuery"
        :students="studentListWithCheckin"
        :loading="isLoadingStudents"
        @quick-check-in="handleQuickCheckIn"
      />
    </template>
  </div>
</template>
