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
 * - LocationPicker.vue - 地图选点
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
import { Card, Button, Input, Select, Badge, Dialog } from '@/components/ui'
import {
  Play, Square, CheckCircle, Clock, Users,
  Search, GraduationCap, AlertTriangle, MapPin
} from 'lucide-vue-next'
import { getErrorMessage } from '@/lib/error'

// 子组件
import LocationPicker from '@/components/teacher/LocationPicker.vue'
import StudentCheckinGrid from '@/components/teacher/StudentCheckinGrid.vue'
import CheckinStats from '@/components/teacher/CheckinStats.vue'

// ===== 状态定义 =====
const className = ref('')
const courseName = ref('')
const studentCode = ref('')
const searchQuery = ref('')

// 地图对话框
const showMapDialog = ref(false)
const locationPickerRef = ref<InstanceType<typeof LocationPicker> | null>(null)
const selectedLocation = ref<{ lat: number; lng: number; name: string } | null>(null)
const checkinRadius = ref(100)

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

const { show, message: toastMessage, variant: toastVariant, success: showSuccessToast, error: showErrorToast } = useToast()

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
    id: s.id,
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
const handleStartSession = () => {
  if (!className.value) {
    showErrorToast('请选择班级')
    return
  }

  showMapDialog.value = true
  // 延迟初始化地图，等待对话框打开
  setTimeout(() => {
    locationPickerRef.value?.initialize()
    locationPickerRef.value?.getCurrentPosition()
  }, 100)
}

const confirmStartSession = async () => {
  if (!selectedLocation.value) {
    showErrorToast('请选择签到位置')
    return
  }

  try {
    await startSession({
      className: className.value,
      courseName: courseName.value || undefined,
      locationLat: selectedLocation.value.lat,
      locationLng: selectedLocation.value.lng,
      locationName: selectedLocation.value.name,
      checkinRadius: checkinRadius.value
    })
    showSuccessToast('课堂已开始！')
    showMapDialog.value = false
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
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">课堂签到</h1>
      <p class="text-white/60">管理您的活跃课堂</p>
    </div>

    <!-- Session status -->
    <Card
      class="border-white/10 p-6"
      :class="isSessionActive ? 'bg-green-500/5 border-green-500/20' : 'bg-white/[0.02]'"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-full"
            :class="isSessionActive ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/60'"
          >
            <Clock class="h-6 w-6" />
          </div>
          <div>
            <h2 class="font-medium text-white">
              {{ isSessionActive ? '课堂进行中' : '暂无活跃课堂' }}
            </h2>
            <p v-if="activeSession" class="text-sm text-white/60">
              {{ activeSession.class_name }} • 开始于 {{ activeSession.start_time }}
            </p>
            <p v-if="activeSession?.location_name" class="text-sm text-blue-400 flex items-center gap-1">
              <MapPin class="h-3 w-3" />
              {{ activeSession.location_name }} ({{ activeSession.checkin_radius || 100 }}米范围)
            </p>
            <p v-else-if="!isSessionActive" class="text-sm text-white/60">
              选择班级开始新课堂
            </p>
          </div>
        </div>
        <div>
          <Button
            v-if="!isSessionActive"
            :loading="isStartingSession"
            @click="handleStartSession"
          >
            <Play class="mr-2 h-4 w-4" />
            开始课堂
          </Button>
          <Button
            v-else
            variant="destructive"
            :loading="isEndingSession"
            @click="handleEndSession"
          >
            <Square class="mr-2 h-4 w-4" />
            结束课堂
          </Button>
        </div>
      </div>
    </Card>

    <!-- Start session form -->
    <Card v-if="!isSessionActive" class="border-white/10 bg-white/[0.02] p-6">
      <h3 class="font-medium text-white">开始新课堂</h3>
      <p class="text-sm text-white/60">选择课程和班级开始上课</p>

      <!-- 班级占用状态 -->
      <div
        v-if="otherOccupiedClasses.length > 0"
        class="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg"
      >
        <p class="text-sm text-yellow-400 flex items-center gap-2">
          <AlertTriangle class="h-4 w-4" />
          以下班级正在被其他教师上课：
        </p>
        <ul class="mt-2 text-sm text-white/70 space-y-1">
          <li v-for="cls in otherOccupiedClasses" :key="cls.class_name">
            {{ cls.class_name }} - {{ cls.teacher_name || '其他教师' }} 老师
          </li>
        </ul>
      </div>

      <div class="mt-4 space-y-4">
        <div class="flex gap-4">
          <Select
            v-model="courseName"
            class="flex-1"
            placeholder="请选择课程（可选）"
            :options="courseOptions"
          />
          <Select
            v-model="className"
            class="flex-1"
            placeholder="请选择班级"
            :options="availableClassOptions"
          />
        </div>
        <Button
          :loading="isStartingSession"
          :disabled="!className"
          class="w-full"
          @click="handleStartSession"
        >
          <Play class="mr-2 h-4 w-4" />
          开始上课
        </Button>
      </div>
    </Card>

    <!-- Active session content -->
    <template v-if="isSessionActive">
      <!-- Check-in form -->
      <Card class="border-white/10 bg-white/[0.02] p-6">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
            <CheckCircle class="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 class="font-medium text-white">学生签到</h3>
            <p class="text-sm text-white/60">输入学生学号进行签到</p>
          </div>
        </div>
        <div class="mt-4 flex gap-4">
          <Input
            v-model="studentCode"
            placeholder="请输入学生学号"
            class="flex-1"
            @keyup.enter="handleCheckIn"
          />
          <Button :loading="isCheckingIn" @click="handleCheckIn">
            <CheckCircle class="mr-2 h-4 w-4" />
            签到
          </Button>
        </div>
      </Card>

      <!-- Stats -->
      <CheckinStats :stats="checkinStats" />

      <!-- Student list -->
      <StudentCheckinGrid
        v-model:search-query="searchQuery"
        :students="studentListWithCheckin"
        :loading="isLoadingStudents"
        @quick-check-in="handleQuickCheckIn"
      />
    </template>

    <!-- Location picker dialog -->
    <Dialog v-model:open="showMapDialog" title="选择签到位置">
      <LocationPicker
        ref="locationPickerRef"
        v-model="selectedLocation"
        v-model:radius="checkinRadius"
        :loading="isStartingSession"
        @confirm="confirmStartSession"
        @cancel="showMapDialog = false"
      />
    </Dialog>

    <!-- Toast -->
    <Dialog v-model:open="show" title="提示">
      <div :class="toastVariant === 'success' ? 'text-green-400' : 'text-red-400'">
        {{ toastMessage }}
      </div>
    </Dialog>
  </div>
</template>
