<script setup lang="ts">
/**
 * 课堂签到页面 - 多班级并行上课支持
 *
 * 功能：
 * - 支持同时管理多个班级课堂
 * - 标签页切换不同班级
 * - 独立管理每个班级的签到状态
 */
import { ref, computed, watch } from 'vue'
import {
  useClassSessions,
  useClassSessionStart,
  useClassSessionEnd,
  useStudentCheckIn,
  useActiveClassSessions,
  useToast,
  useNetworkError
} from '@/composables'
import { useClasses, useClassStudents } from '@/composables/useClasses'
import { useSchedules } from '@/composables/useSchedules'
import { useTodayCheckins } from '@/composables/useCheckins'
import { useAuthStore } from '@/stores'
import { Card, Button, Input, Select, Badge, NetworkErrorBanner, Dialog } from '@/components/ui'
import {
  Play, Square, CheckCircle, Clock, X, Plus,
  AlertTriangle, Users
} from 'lucide-vue-next'
import { getErrorMessage } from '@/lib/error'
import type { ClassSessionInfo } from '@/types'

// 子组件
import StudentCheckinGrid from '@/components/teacher/StudentCheckinGrid.vue'
import CheckinStats from '@/components/teacher/CheckinStats.vue'

// ===== 状态定义 =====
const className = ref('')
const courseName = ref('')
const studentCode = ref('')
const searchQuery = ref('')
const showStartForm = ref(false)

// 新增状态
const softLimitWarning = ref(false)   // 显示软限制警告
const showEndConfirm = ref(false)     // 显示结束课堂确认弹窗
const endConfirmClassName = ref('')   // 待结束的班级名称

// 常量定义
const SOFT_LIMIT = 5  // 软限制：5个班级

// 当前选中的课堂标签
const activeTab = ref<string>('')

// ===== 获取数据 =====
const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)

// 网络错误处理
const { networkError, setError, clearError } = useNetworkError()

// 获取所有活跃课堂（多班级支持）
const { data: activeSessions, error: sessionsError, refetch: refetchSessions } = useClassSessions()
const { mutateAsync: startSession, isPending: isStartingSession } = useClassSessionStart()
const { mutateAsync: endSession, isPending: isEndingSession } = useClassSessionEnd()

// 重试所有查询
const handleRetry = () => {
  clearError()
  refetchSessions()
}

// 监听网络错误
watch(() => sessionsError.value, (err) => {
  if (err) {
    setError(err as Error)
  }
})

const { data: allActiveSessions } = useActiveClassSessions()
const { data: classList } = useClasses()
const { data: schedules } = useSchedules()

// 当前选中的课堂
const selectedSession = computed<ClassSessionInfo | null>(() => {
  if (!activeSessions.value || activeSessions.value.length === 0) return null
  if (activeSessions.value.length === 1) return activeSessions.value[0]
  if (!activeTab.value) return activeSessions.value[0]
  return activeSessions.value.find((s: ClassSessionInfo) => s.class_name === activeTab.value) || activeSessions.value[0]
})

// 当前选中课堂的班级名称
const selectedClassName = computed(() => selectedSession.value?.class_name || '')

const { data: classStudents, isPending: isLoadingStudents } = useClassStudents(selectedClassName)
const { data: todayCheckins, refetch: refetchCheckins } = useTodayCheckins(selectedClassName)

const { mutateAsync: checkIn, isPending: isCheckingIn } = useStudentCheckIn(selectedClassName)

const { success: showSuccessToast, error: showErrorToast } = useToast()

// ===== 计算属性 =====
const isSessionActive = computed(() => activeSessions.value && activeSessions.value.length > 0)

// 是否有多个活跃课堂
const hasMultipleSessions = computed(() => (activeSessions.value?.length || 0) > 1)

// 新增计算属性
const sessionCount = computed(() => activeSessions.value?.length || 0)
const nearSoftLimit = computed(() => sessionCount.value >= 3)
const atSoftLimit = computed(() => sessionCount.value >= SOFT_LIMIT)

// 其他教师占用的班级
const otherOccupiedClasses = computed(() => {
  if (!allActiveSessions.value) return []
  const currentUserId = currentUser.value?.id
  return allActiveSessions.value.filter(s => s.teacher_id !== currentUserId)
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
    allActiveSessions.value?.map(s => [s.class_name, s.teacher_name]) || []
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

// 切换标签时更新
const handleTabChange = (className: string) => {
  activeTab.value = className
}

// ===== 事件处理 =====
const handleStartSession = async () => {
  if (!className.value) {
    showErrorToast('请选择班级')
    return
  }

  // 软限制检查：达到限制时显示强制确认
  if (atSoftLimit.value && !softLimitWarning.value) {
    softLimitWarning.value = true
    return
  }

  try {
    await startSession({
      className: className.value,
      courseName: courseName.value || undefined
    })
    showSuccessToast('课堂已开始！')
    // 切换到新开始的课堂
    activeTab.value = className.value
    className.value = ''
    courseName.value = ''
    // 关闭开始新课堂表单
    showStartForm.value = false
    // 重置软限制警告
    softLimitWarning.value = false
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '开始课堂失败')
  }
}

const handleEndSession = async (sessionClassName?: string) => {
  // 显示确认弹窗
  endConfirmClassName.value = sessionClassName || selectedSession.value?.class_name || ''
  showEndConfirm.value = true
}

const confirmEndSession = async () => {
  showEndConfirm.value = false
  try {
    await endSession({ className: endConfirmClassName.value })
    showSuccessToast(endConfirmClassName.value ? `${endConfirmClassName.value} 课堂已结束！` : '课堂已结束！')
    // 如果结束的是当前选中的标签，重置标签选择
    if (endConfirmClassName.value === activeTab.value) {
      activeTab.value = ''
    }
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '结束课堂失败')
  }
}

// 确认弹窗统计
const endConfirmStats = computed(() => ({
  checkedIn: checkinStats.value.checkedIn,
  notCheckedIn: checkinStats.value.notCheckedIn,
}))

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

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div>
    <!-- Network Error Banner -->
    <NetworkErrorBanner
      v-if="networkError"
      :message="networkError.message || '网络连接失败，数据同步异常'"
      @retry="handleRetry"
      @dismiss="clearError"
    />

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
              {{ isSessionActive ? `课堂进行中 (${activeSessions?.length}个班级)` : '暂无活跃课堂' }}
            </h2>
            <p
              v-if="!isSessionActive"
              class="text-sm text-white/60"
            >
              选择班级开始新课堂
            </p>
            <p
              v-else-if="selectedSession"
              class="text-sm text-white/60 truncate"
            >
              当前: {{ selectedSession.class_name }} • 开始于 {{ formatTime(selectedSession.start_time) }}
            </p>
          </div>
        </div>
        <div class="flex-shrink-0 flex gap-2">
          <template v-if="!isSessionActive">
            <Button
              :loading="isStartingSession"
              class="w-full sm:w-auto min-h-[44px]"
              @click="handleStartSession"
            >
              <Play class="mr-2 h-4 w-4" />
              开始课堂
            </Button>
          </template>
          <template v-else-if="!hasMultipleSessions">
            <Button
              variant="outline"
              :loading="isStartingSession"
              class="w-full sm:w-auto min-h-[44px] border-white/20 text-white hover:bg-white/10"
              @click="showStartForm = true"
            >
              <Plus class="mr-2 h-4 w-4" />
              开始新课堂
            </Button>
            <Button
              variant="destructive"
              :loading="isEndingSession"
              class="w-full sm:w-auto min-h-[44px]"
              @click="handleEndSession()"
            >
              <Square class="mr-2 h-4 w-4" />
              结束课堂
            </Button>
          </template>
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

    <!-- Multi-session tabs -->
    <div
      v-if="hasMultipleSessions"
      class="mb-5"
    >
      <div class="flex flex-wrap gap-2">
        <div
          v-for="session in activeSessions"
          :key="session.class_name"
          class="flex items-center px-4 py-2 rounded-lg border transition-all duration-200"
          :class="activeTab === session.class_name || (!activeTab && session === activeSessions?.[0])
            ? 'bg-primary/20 border-primary text-white'
            : 'bg-white/5 border-white/10 text-white/70'"
        >
          <button
            class="flex items-center gap-2 flex-1"
            @click="handleTabChange(session.class_name)"
          >
            <Users class="h-4 w-4" />
            <span>{{ session.class_name }}</span>
            <Badge
              variant="secondary"
              class="text-xs"
            >
              {{ session.course_name || '未命名课程' }}
            </Badge>
          </button>
          <button
            class="ml-2 p-1 rounded hover:bg-white/20 text-white/50 hover:text-white transition-colors"
            title="结束此课堂"
            @click="handleEndSession(session.class_name)"
          >
            <X class="h-3 w-3" />
          </button>
        </div>
      </div>
    </div>

    <!-- 开始新课堂表单 (在有一个课堂进行时显示) -->
    <Card
      v-if="isSessionActive && showStartForm"
      class="p-4 md:p-6 mb-5 border-primary/30 bg-primary/5"
    >
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="font-medium text-white text-base md:text-lg">
            开始新课堂
          </h3>
          <p class="text-sm text-white/60">
            同时管理另一个班级
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          class="text-white/60 hover:text-white"
          @click="showStartForm = false"
        >
          <X class="h-4 w-4" />
        </Button>
      </div>

      <!-- 软限制警告 -->
      <div
        v-if="nearSoftLimit && !atSoftLimit"
        class="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg"
      >
        <p class="text-sm text-yellow-400 flex items-center gap-2">
          <AlertTriangle class="h-4 w-4 flex-shrink-0" />
          您已开启{{ sessionCount }}个课堂，接近软限制（{{ SOFT_LIMIT }}个）
        </p>
      </div>

      <!-- 强制软限制确认 -->
      <div
        v-if="softLimitWarning"
        class="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg"
      >
        <p class="text-sm text-red-400 mb-2">
          您已达到软限制（{{ SOFT_LIMIT }}个课堂），继续开启可能影响性能。
        </p>
        <div class="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            class="border-red-500/30 text-red-400 hover:bg-red-500/10"
            @click="handleStartSession"
          >
            仍要继续
          </Button>
          <Button
            size="sm"
            variant="ghost"
            class="text-white/60"
            @click="softLimitWarning = false"
          >
            取消
          </Button>
        </div>
      </div>

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
      <div class="flex gap-2">
        <Button
          :loading="isStartingSession"
          :disabled="!className"
          class="flex-1 min-h-[44px]"
          @click="handleStartSession"
        >
          <Play class="mr-2 h-4 w-4" />
          开始上课
        </Button>
        <Button
          variant="outline"
          class="min-h-[44px] border-white/20 text-white hover:bg-white/10"
          @click="showStartForm = false"
        >
          取消
        </Button>
      </div>
    </Card>

    <!-- Active session content -->
    <template v-if="isSessionActive && selectedSession">
      <!-- Selected session info (for multi-session) -->
      <Card
        v-if="hasMultipleSessions"
        class="p-4 mb-5 bg-gradient-to-r from-primary/10 to-transparent border-primary/20"
      >
        <div class="flex items-center justify-between">
          <div>
            <h3 class="font-medium text-white text-lg">
              {{ selectedSession.class_name }}
            </h3>
            <p class="text-sm text-white/60">
              {{ selectedSession.course_name || '未命名课程' }} • 开始于 {{ formatTime(selectedSession.start_time) }}
            </p>
          </div>
          <Button
            variant="destructive"
            size="sm"
            :loading="isEndingSession"
            @click="handleEndSession(selectedSession.class_name)"
          >
            <Square class="mr-2 h-4 w-4" />
            结束此课堂
          </Button>
        </div>
      </Card>

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
      <CheckinStats :stats="checkinStats" class="mb-5" />

      <!-- Student list -->
      <StudentCheckinGrid
        v-model:search-query="searchQuery"
        :students="studentListWithCheckin"
        :loading="isLoadingStudents"
        @quick-check-in="handleQuickCheckIn"
      />
    </template>

    <!-- End Session Confirmation Dialog -->
    <Dialog
      :open="showEndConfirm"
      title="确认结束课堂"
      @update:open="showEndConfirm = $event"
    >
      <template #description>
        确定要结束【{{ endConfirmClassName }}】的课堂吗？
      </template>
      <div class="py-4">
        <div class="flex justify-center gap-8 text-center">
          <div>
            <p class="text-2xl font-bold text-green-400">{{ endConfirmStats.checkedIn }}</p>
            <p class="text-sm text-white/60">已签到</p>
          </div>
          <div>
            <p class="text-2xl font-bold text-red-400">{{ endConfirmStats.notCheckedIn }}</p>
            <p class="text-sm text-white/60">未签到</p>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex gap-2 justify-end">
          <Button
            variant="outline"
            @click="showEndConfirm = false"
          >
            取消
          </Button>
          <Button
            variant="destructive"
            @click="confirmEndSession"
          >
            确认结束
          </Button>
        </div>
      </template>
    </Dialog>

  </div>
</template>
