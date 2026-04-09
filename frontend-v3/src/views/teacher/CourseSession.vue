<script setup lang="ts">
/**
 * CourseSession 课堂签到页面 - 基于 CourseSession 体系
 *
 * 功能：
 * - 支持同时管理多个班级课堂
 * - 标签页切换不同班级
 * - 独立管理每个班级的签到状态
 * - 顶部今日课表快捷开始
 */
import { ref, computed, watch } from 'vue'
import {
  useCourseSessions,
  useCourseSessionStart,
  useCourseSessionEnd,
  useStudentCheckIn,
  useActiveClassSessions,
  useTodaySchedules,
  useToast,
  useNetworkError
} from '@/composables'
import { useClasses, useClassStudents } from '@/composables/useClasses'
import { useSessionCheckins } from '@/composables/useCheckins'
import { useTeacherCourses } from '@/composables/useTeacherCourses'
import { useAuthStore } from '@/stores'
import { Card, Button, Input, Select, Badge, NetworkErrorBanner, Dialog } from '@/components/ui'
import {
  Play, Square, CheckCircle, Clock, X, Plus,
  AlertTriangle, Users
} from 'lucide-vue-next'
import { getErrorMessage } from '@/lib/error'
import type { CourseSession } from '@/types'

// 子组件
import StudentCheckinGrid from '@/components/teacher/StudentCheckinGrid.vue'
import CheckinStats from '@/components/teacher/CheckinStats.vue'

// ===== 卡片主题辅助函数 - 统一使用 Indigo 主题 =====
const getCardStyle = () => {
  return {
    backgroundColor: 'var(--card-indigo-bg)',
    borderColor: 'var(--card-indigo-border)',
    '--tw-shadow-color': 'var(--card-indigo-shadow)',
  } as Record<string, string>
}

const getCardIconStyle = () => {
  return {
    backgroundColor: 'var(--card-indigo-icon-bg)',
    color: 'var(--card-indigo-icon-text)',
  }
}

const getCardGlowStyle = () => {
  return {
    backgroundColor: 'var(--card-indigo-glow)',
  }
}

// ===== 辅助函数 =====

/**
 * 获取课堂状态样式
 * @param isActive 是否进行中
 * @returns 主题样式配置
 */
const getSessionStatusTheme = (isActive: boolean) => {
  if (isActive) {
    return {
      icon: CheckCircle,
      titleColor: 'text-green-400',
      pulse: true
    }
  }
  return {
    icon: Clock,
    titleColor: 'text-black',
    pulse: false
  }
}

/**
 * 获取签到率颜色
 * @param rate 签到率 (0-100)
 * @returns 颜色主题
 */
const getCheckinRateColor = (rate: number): string => {
  if (rate >= 90) return 'text-green-400'
  if (rate >= 70) return 'text-blue-400'
  if (rate >= 50) return 'text-orange-400'
  return 'text-red-400'
}

/**
 * 获取签到率进度条颜色
 * @param rate 签到率 (0-100)
 * @returns 背景色类名
 */
const getCheckinRateBarColor = (rate: number): string => {
  if (rate >= 90) return 'bg-green-400'
  if (rate >= 70) return 'bg-blue-400'
  if (rate >= 50) return 'bg-orange-400'
  return 'bg-red-400'
}

/**
 * 格式化持续时间
 * @param startTime 开始时间字符串
 * @returns 格式化后的持续时间 (如: 45分钟)
 */
const formatDuration = (startTime: string): string => {
  if (!startTime) return ''
  const start = new Date(startTime)
  const now = new Date()
  const diffMs = now.getTime() - start.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return '刚开始'
  if (diffMins < 60) return `${diffMins}分钟`
  const hours = Math.floor(diffMins / 60)
  const mins = diffMins % 60
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
}

// ===== 状态定义 =====
const className = ref('')
const courseName = ref('')
const studentCode = ref('')
const searchQuery = ref('')
const showStartForm = ref(false)

// 新增状态
const softLimitWarning = ref(false)   // 显示软限制警告
const showEndConfirm = ref(false)     // 显示结束课堂确认弹窗
const endConfirmSessionId = ref<number | null>(null)   // 待结束的课堂ID
const endConfirmClassName = ref('')   // 待结束的班级名称（用于提示）

// 常量定义
const SOFT_LIMIT = 5  // 软限制：5个班级

// 当前选中的课堂标签
const activeTab = ref<number>(0)

// ===== 获取数据 =====
const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)

// 网络错误处理
const { networkError, setError, clearError } = useNetworkError()

// 获取所有活跃课堂（多班级支持）
const { data: activeSessions, error: sessionsError, refetch: refetchSessions } = useCourseSessions()
const { mutateAsync: startSession, isPending: isStartingSession } = useCourseSessionStart()
const { mutateAsync: endSession, isPending: isEndingSession } = useCourseSessionEnd()

// 今日课表（用于快捷开始）
const { data: todaySchedules } = useTodaySchedules()

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

// 当前选中的课堂
const selectedSession = computed<CourseSession | null>(() => {
  if (!activeSessions.value || activeSessions.value.length === 0) return null
  if (activeSessions.value.length === 1) return activeSessions.value[0]
  if (!activeTab.value) return activeSessions.value[0]
  return activeSessions.value.find((s: CourseSession) => s.id === activeTab.value) || activeSessions.value[0]
})

// 当前选中课堂的班级名称和ID
const selectedClassName = computed(() => selectedSession.value?.class_name || '')
const selectedSessionId = computed(() => selectedSession.value?.id)

const { data: classStudents, isPending: isLoadingStudents } = useClassStudents(selectedClassName)
const { data: sessionCheckins, refetch: refetchCheckins } = useSessionCheckins(selectedSessionId)

const { mutateAsync: checkIn, isPending: isCheckingIn } = useStudentCheckIn(selectedSessionId)

const { success: showSuccessToast, error: showErrorToast } = useToast()
const { data: teacherCourses } = useTeacherCourses()

// 正在快速签到的学生ID集合（防止重复点击）
const checkingStudentIds = ref<Set<string>>(new Set())

// ===== 计算属性 =====
const isSessionActive = computed(() => activeSessions.value && activeSessions.value.some((s: CourseSession) => s.status === 'active'))

// 活跃的课堂列表
const activeCourseSessions = computed(() => {
  if (!activeSessions.value) return []
  return activeSessions.value.filter((s: CourseSession) => s.status === 'active')
})

// 是否有多个活跃课堂
const hasMultipleSessions = computed(() => (activeCourseSessions.value?.length || 0) > 1)

// 新增计算属性
const sessionCount = computed(() => activeCourseSessions.value?.length || 0)
const nearSoftLimit = computed(() => sessionCount.value >= 3)
const atSoftLimit = computed(() => sessionCount.value >= SOFT_LIMIT)

// 其他教师占用的班级
const otherOccupiedClasses = computed(() => {
  if (!allActiveSessions.value || !currentUser.value?.id) return []
  const currentUserId = Number(currentUser.value.id)
  return allActiveSessions.value.filter((s: any) => s.teacher_id !== currentUserId)
})

// 班级选项
const availableClassOptions = computed(() => {
  if (!classList.value) return []
  const occupiedMap = new Map(
    allActiveSessions.value?.map((s: any) => [s.class_name, s.teacher_name]) || []
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

// 今日可快捷开始的课表
const quickStartSchedules = computed(() => {
  if (!todaySchedules.value) return []
  return todaySchedules.value.filter(s => s.session_status === 'none')
})

// 已签到学生ID集合
const checkedInStudentIds = computed(() => {
  if (!sessionCheckins.value) return new Set()
  return new Set(sessionCheckins.value.map((c: any) => c.student_id))
})

// 学生列表（带签到状态）
const studentListWithCheckin = computed(() => {
  if (!classStudents.value) return []

  const checkinTimeMap = new Map<string, string>()
  sessionCheckins.value?.forEach((c: any) => {
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
const handleTabChange = (sessionId: number) => {
  activeTab.value = sessionId
}

// 快捷开始课堂
const handleQuickStart = async (schedule: any) => {
  try {
    await startSession({
      className: schedule.class_name,
      courseName: schedule.course_name,
      scheduleId: schedule.id,
    })
    showSuccessToast('课堂已开始！')
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '开始课堂失败')
  }
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
      courseName: courseName.value || undefined,
      scheduleId: undefined,
    })
    showSuccessToast('课堂已开始！')
    activeTab.value = 0
    className.value = ''
    courseName.value = ''
    showStartForm.value = false
    softLimitWarning.value = false
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '开始课堂失败')
  }
}

const handleEndSession = async (session?: CourseSession) => {
  endConfirmSessionId.value = session?.id ?? selectedSession.value?.id ?? null
  endConfirmClassName.value = session?.class_name || selectedSession.value?.class_name || ''
  showEndConfirm.value = true
}

const confirmEndSession = async () => {
  showEndConfirm.value = false
  if (endConfirmSessionId.value == null) return
  try {
    await endSession(endConfirmSessionId.value)
    showSuccessToast(endConfirmClassName.value ? `${endConfirmClassName.value} 课堂已结束！` : '课堂已结束！')
    if (endConfirmSessionId.value === activeTab.value) {
      activeTab.value = 0
    }
    endConfirmSessionId.value = null
    endConfirmClassName.value = ''
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
    await refetchCheckins()
    showSuccessToast('学生签到成功！')
    studentCode.value = ''
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '签到失败')
  }
}

const handleQuickCheckIn = async (studentId: string) => {
  if (checkingStudentIds.value.has(studentId)) return
  checkingStudentIds.value.add(studentId)
  try {
    await checkIn(studentId)
    await refetchCheckins()
    showSuccessToast('签到成功！')
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '签到失败')
  } finally {
    checkingStudentIds.value.delete(studentId)
  }
}

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 课堂状态主题
const sessionStatusTheme = computed(() => getSessionStatusTheme(!!isSessionActive.value))

// 当前课堂签到率
const currentCheckinRate = computed(() => {
  if (checkinStats.value.total === 0) return 0
  return Math.round((checkinStats.value.checkedIn / checkinStats.value.total) * 100)
})

// 当前课堂持续时间
const sessionDuration = computed(() => {
  if (!selectedSession.value?.start_time) return ''
  return formatDuration(selectedSession.value.start_time)
})

// source_type 显示文本和颜色
const getSourceTypeBadge = (sourceType: string) => {
  switch (sourceType) {
    case 'scheduled':
      return { text: '自动', class: 'bg-[#fafafa] text-[#525252] border-[#e5e5e5]' }
    case 'manual':
      return { text: '手动', class: 'bg-[#fafafa] text-[#737373] border-[#e5e5e5]' }
    case 'makeup':
      return { text: '补课', class: 'bg-[#f5f5f5] text-[#525252] border-[#e5e5e5]' }
    default:
      return { text: sourceType, class: 'bg-[#fafafa] text-[#737373] border-[#e5e5e5]' }
  }
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
      <h1 class="text-2xl font-medium text-black">
        课堂签到
      </h1>
      <p class="text-[#737373]">
        管理您的活跃课堂
      </p>
    </div>

    <!-- 今日课表快捷开始 - Indigo 主题 -->
    <Card
      v-if="quickStartSchedules.length > 0"
      class="relative overflow-hidden p-4 md:p-6 mb-5"
      :style="getCardStyle()"
    >
      <div class="relative z-10">
        <h3 class="font-medium text-black text-base md:text-lg mb-3">
          今日课表
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div
            v-for="schedule in quickStartSchedules"
            :key="schedule.id"
            class="rounded-lg border border-[#e5e5e5] bg-white p-3 flex items-center justify-between hover:bg-[#fafafa]"
          >
          <div>
            <p class="text-sm text-black font-medium">{{ schedule.course_name }}</p>
            <p class="text-xs text-[#a3a3a3]">{{ schedule.class_name }} · {{ schedule.start_time?.slice(0, 5) }}</p>
          </div>
          <Button
            size="sm"
            class="bg-green-500 hover:bg-green-600 text-white"
            :loading="isStartingSession"
            @click="handleQuickStart(schedule)"
          >
            <Play class="mr-1 h-3.5 w-3.5" />
            开始
          </Button>
        </div>
      </div>
      </div>
      <!-- 背景装饰 -->
    </Card>

    <!-- Session status - 课堂状态卡片 -->
    <Card
      class="relative overflow-hidden p-4 md:p-6 mb-5"
      :style="isSessionActive ? { backgroundColor: 'var(--card-success-bg)', borderColor: 'var(--card-success-border)', '--tw-shadow-color': 'var(--card-success-shadow)' } : { backgroundColor: 'rgba(255,255,255,0.02)', borderColor: '#e5e5e5' }"
    >
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="flex items-center gap-3 md:gap-4">
          <!-- 状态图标 -->
          <div
            class="relative flex h-12 w-12 md:h-14 md:w-14 items-center justify-center rounded-xl flex-shrink-0 transition-all duration-300"
            :style="isSessionActive ? { backgroundColor: 'var(--card-success-icon-bg)', color: 'var(--card-success-icon-text)' } : { backgroundColor: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.6)' }"
          >
            <component
              :is="sessionStatusTheme.icon"
              class="h-6 w-6 md:h-7 md:w-7"
            />
            <!-- 脉冲动画 - 课堂进行中 -->
            <span
              v-if="sessionStatusTheme.pulse"
              class="absolute inline-flex h-12 w-12 md:h-14 md:w-14 rounded-xl bg-green-400/20 animate-ping"
            />
          </div>

          <!-- 状态信息 -->
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 flex-wrap">
              <h2
                class="font-medium text-lg"
                :class="isSessionActive ? 'text-green-400' : 'text-black'"
              >
                {{ isSessionActive ? '课堂进行中' : '暂无活跃课堂' }}
              </h2>
              <!-- 多班级标签 -->
              <Badge
                v-if="isSessionActive && sessionCount > 1"
                variant="secondary"
                class="bg-green-500/20 text-green-400 border-green-500/30"
              >
                {{ sessionCount }}个班级
              </Badge>
              <!-- 持续时间标签 -->
              <Badge
                v-if="isSessionActive && sessionDuration"
                variant="secondary"
                class="bg-[#fafafa] text-[#737373]"
              >
                <Clock class="h-3 w-3 mr-1" />
                {{ sessionDuration }}
              </Badge>
            </div>
            <p
              v-if="!isSessionActive"
              class="text-sm text-[#737373] mt-0.5"
            >
              选择班级开始新课堂
            </p>
            <p
              v-else-if="selectedSession"
              class="text-sm text-[#737373] mt-0.5 truncate"
            >
              <span class="text-black">{{ selectedSession.class_name }}</span>
              <span class="mx-1.5 text-[#a3a3a3]">•</span>
              <span>{{ selectedSession.course_name || '未命名课程' }}</span>
              <span class="mx-1.5 text-[#a3a3a3]">•</span>
              <span>开始于 {{ formatTime(selectedSession.start_time) }}</span>
              <template v-if="selectedSession.session_code">
                <span class="mx-1.5 text-[#a3a3a3]">•</span>
                <span>课堂码 {{ selectedSession.session_code }}</span>
              </template>
              <template v-if="selectedSession.source_type">
                <span class="mx-1.5 text-[#a3a3a3]">•</span>
                <Badge
                  variant="secondary"
                  class="text-[10px] px-1 py-0"
                  :class="getSourceTypeBadge(selectedSession.source_type).class"
                >
                  {{ getSourceTypeBadge(selectedSession.source_type).text }}
                </Badge>
              </template>
            </p>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex-shrink-0 flex gap-2">
          <template v-if="!isSessionActive">
            <Button
              :loading="isStartingSession"
              class="w-full sm:w-auto min-h-[44px] bg-green-500 hover:bg-green-600 text-white"
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
              class="w-full sm:w-auto min-h-[44px] border-[#e5e5e5] text-black hover:bg-[#fafafa]"
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

      <!-- 背景装饰 -->
      <div
        v-if="isSessionActive"
        class="absolute -right-4 -bottom-4 h-16 w-16 rounded-full blur-2xl opacity-30"
        :style="{ backgroundColor: 'var(--card-success-glow)' }"
      />

      <!-- 签到进度条 - 仅在活跃课堂显示 -->
      <div
        v-if="isSessionActive && checkinStats.total > 0"
        class="mt-4 pt-4 border-t border-[#e5e5e5]"
      >
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm text-[#737373]">签到进度</span>
          <span
            class="text-sm font-medium"
            :class="getCheckinRateColor(currentCheckinRate)"
          >
            {{ checkinStats.checkedIn }}/{{ checkinStats.total }} ({{ currentCheckinRate }}%)
          </span>
        </div>
        <div class="h-2 bg-[#f5f5f5] rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500 ease-out"
            :class="getCheckinRateBarColor(currentCheckinRate)"
            :style="{ width: `${currentCheckinRate}%` }"
          />
        </div>
      </div>
    </Card>

    <!-- Start session form - Indigo 主题 -->
    <Card
      v-if="!isSessionActive"
      class="relative overflow-hidden p-4 md:p-6 mb-5"
      :style="getCardStyle()"
    >
      <div class="relative z-10">
        <h3 class="font-medium text-black text-base md:text-lg">
          开始新课堂
        </h3>
        <p class="text-sm text-[#737373]">
          选择班级开始上课
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
        <ul class="mt-2 text-sm text-[#737373] space-y-1">
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
            placeholder="选择课程（可选）"
            :options="teacherCourses?.map(c => ({ label: c, value: c })) || []"
            clearable
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
      </div>
    </Card>

    <!-- Multi-session selector (Responsive) -->
    <div
      v-if="hasMultipleSessions"
      class="mb-5"
    >
      <!-- Desktop: Tabs -->
      <div class="hidden md:flex flex-wrap gap-2">
        <div
          v-for="session in activeCourseSessions"
          :key="session.id"
          class="flex items-center px-4 py-2 rounded-lg border"
          :class="activeTab === session.id || (!activeTab && session === activeCourseSessions?.[0])
            ? 'bg-primary/20 border-primary text-black'
            : 'bg-white border-[#e5e5e5] text-[#737373]'"
        >
          <button
            class="flex items-center gap-2 flex-1"
            @click="handleTabChange(session.id)"
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
            class="ml-2 p-1 rounded hover:bg-[#f5f5f5] text-[#a3a3a3] hover:text-black"
            title="结束此课堂"
            @click="handleEndSession(session)"
          >
            <X class="h-3 w-3" />
          </button>
        </div>
      </div>

      <!-- Mobile: Dropdown -->
      <div class="md:hidden">
        <label class="block text-sm text-[#737373] mb-2">当前课堂</label>
        <Select
          :model-value="activeTab || activeCourseSessions?.[0]?.id"
          class="w-full"
          placeholder="选择课堂"
          :options="activeCourseSessions?.map(s => ({
            value: s.id,
            label: `${s.class_name} ${s.course_name ? '(' + s.course_name + ')' : ''}`
          })) || []"
          @update:model-value="(v) => handleTabChange(Number(v))"
        />
      </div>
    </div>

    <!-- 开始新课堂表单 (在有一个课堂进行时显示) -->
    <Card
      v-if="isSessionActive && showStartForm"
      class="relative overflow-hidden p-4 md:p-6 mb-5"
      :style="getCardStyle()"
    >
      <div class="relative z-10 flex items-center justify-between mb-4">
        <div>
          <h3 class="font-medium text-black text-base md:text-lg">
            开始新课堂
          </h3>
          <p class="text-sm text-[#737373]">
            同时管理另一个班级
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          class="text-[#737373] hover:text-black"
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
            class="text-[#737373]"
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
          placeholder="选择课程（可选）"
          :options="teacherCourses?.map(c => ({ label: c, value: c })) || []"
          clearable
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
          class="min-h-[44px] border-[#e5e5e5] text-black hover:bg-[#fafafa]"
          @click="showStartForm = false"
        >
          取消
        </Button>
      </div>
    </Card>

    <!-- Active session content -->
    <template v-if="isSessionActive && selectedSession">
      <!-- Selected session info (for multi-session) - Indigo 主题 -->
      <Card
        v-if="hasMultipleSessions"
        class="relative overflow-hidden p-4 mb-5"
        :style="getCardStyle()"
      >
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <h3 class="font-medium text-black text-lg">
              {{ selectedSession.class_name }}
            </h3>
            <p class="text-sm text-[#737373]">
              {{ selectedSession.course_name || '未命名课程' }} · 开始于 {{ formatTime(selectedSession.start_time) }}
              <template v-if="selectedSession.session_code">
                · 课堂码 {{ selectedSession.session_code }}
              </template>
              <template v-if="selectedSession.source_type">
                · <Badge
                  variant="secondary"
                  class="text-[10px] px-1 py-0"
                  :class="getSourceTypeBadge(selectedSession.source_type).class"
                >
                  {{ getSourceTypeBadge(selectedSession.source_type).text }}
                </Badge>
              </template>
            </p>
          </div>
          <Button
            variant="destructive"
            size="sm"
            :loading="isEndingSession"
            @click="handleEndSession(selectedSession)"
          >
            <Square class="mr-2 h-4 w-4" />
            结束此课堂
          </Button>
        </div>
      </Card>

      <!-- Check-in form - Indigo 主题 -->
      <Card class="relative overflow-hidden p-4 md:p-6 mb-5" :style="getCardStyle()">
        <div class="relative z-10 flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full flex-shrink-0" :style="getCardIconStyle()">
            <CheckCircle class="h-5 w-5" :style="{ color: 'var(--card-indigo-icon-text)' }" />
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="font-medium text-black">
              学生签到
            </h3>
            <p class="text-sm text-[#737373]">
              输入学生学号进行签到
            </p>
          </div>
        </div>
        <div class="relative z-10 mt-4 flex flex-col sm:flex-row gap-3 sm:gap-4">
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
        :checking-student-ids="Array.from(checkingStudentIds)"
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
            <p class="text-sm text-[#737373]">已签到</p>
          </div>
          <div>
            <p class="text-2xl font-bold text-red-400">{{ endConfirmStats.notCheckedIn }}</p>
            <p class="text-sm text-[#737373]">未签到</p>
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
