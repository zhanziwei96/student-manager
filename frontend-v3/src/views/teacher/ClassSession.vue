<script setup lang="ts">
import { ref, computed } from 'vue'
import { useClassSession, useClassSessionStart, useClassSessionEnd, useStudentCheckIn, useActiveClassSessions, useToast } from '@/composables'
import { useClasses, useClassStudents } from '@/composables/useClasses'
import { useSchedules } from '@/composables/useSchedules'
import { useTodayCheckins } from '@/composables/useCheckins'
import { useAuthStore } from '@/stores'
import { Card, Button, Input, Select, Badge } from '@/components/ui'
import { Play, Square, CheckCircle, Clock, Users, Search, GraduationCap, AlertTriangle } from 'lucide-vue-next'
import { formatTime } from '@/lib/date'
import { Toast } from '@/components/ui'
import { getErrorMessage } from '@/lib/error'

const className = ref('')
const courseName = ref('')
const studentCode = ref('')
const searchQuery = ref('')

// 获取当前用户信息
const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)

const { data: activeSession } = useClassSession()
const { mutateAsync: startSession, isPending: isStartingSession } = useClassSessionStart()
const { mutateAsync: endSession, isPending: isEndingSession } = useClassSessionEnd()
const { mutateAsync: checkIn, isPending: isCheckingIn } = useStudentCheckIn(computed(() => activeSession.value?.class_name || ''))

// 获取活跃课堂列表
const { data: activeSessions } = useActiveClassSessions()

// 其他教师占用的班级（排除当前用户的）
const otherOccupiedClasses = computed(() => {
  if (!activeSessions.value) return []
  const currentUserId = currentUser.value?.id
  // 排除当前教师开启的所有课堂（不只是当前活跃课堂）
  return activeSessions.value.filter(s => s.teacher_id !== currentUserId)
})

// 可用的班级选项（被占用的标记为禁用）
const availableClassOptions = computed(() => {
  if (!classList.value) return []
  const occupiedMap = new Map(activeSessions.value?.map(s => [s.class_name, s.teacher_name]) || [])
  
  return classList.value.map(cls => {
    const teacherName = occupiedMap.get(cls.name)
    return {
      value: cls.name,
      label: teacherName ? `${cls.name} (已被 ${teacherName} 老师占用)` : cls.name,
      disabled: !!teacherName
    }
  })
})

// 获取班级列表
const { data: classList } = useClasses()

// 获取课程列表（用于选择）
const { data: schedules } = useSchedules()

// 可选的课程列表（根据教师分配的班级关联）
const courseOptions = computed(() => {
  if (!schedules.value) return []
  const courseNames = new Set(schedules.value.map(s => s.course_name).filter(Boolean))
  return Array.from(courseNames).map(name => ({ value: name, label: name }))
})

// 获取选中班级的学生列表
const { data: classStudents, isPending: isLoadingStudents } = useClassStudents(computed(() => activeSession.value?.class_name || ''))

// 获取当前课堂的签到记录
const { data: todayCheckins, refetch: refetchCheckins } = useTodayCheckins(computed(() => activeSession.value?.class_name || ''))

const { show, message: toastMessage, variant: toastVariant, success: showSuccessToast, error: showErrorToast } = useToast()



const isSessionActive = computed(() => !!activeSession.value)

// 已签到学生ID集合
const checkedInStudentIds = computed(() => {
  if (!todayCheckins.value) return new Set()
  return new Set(todayCheckins.value.map(c => c.student_id))
})

// REVIEW-P1: 预计算学生列表分组，避免在模板中重复 filter
const studentListWithCheckin = computed(() => {
  if (!classStudents.value) return []
  
  // 创建签到时间映射
  const checkinTimeMap = new Map<string, string>()
  if (todayCheckins.value) {
    todayCheckins.value.forEach(c => {
      checkinTimeMap.set(c.student_id, c.checkin_time)
    })
  }
  
  // 添加签到状态和时间
  let students = classStudents.value.map(s => ({
    ...s,
    checkedIn: checkedInStudentIds.value.has(s.student_id),
    checkinTime: checkinTimeMap.get(s.student_id)
  }))
  
  // 搜索过滤
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    students = students.filter(s => 
      s.name.toLowerCase().includes(query) ||
      s.student_id.toLowerCase().includes(query)
    )
  }
  
  // 按签到状态排序（未签到在前）
  return students.sort((a, b) => (a.checkedIn === b.checkedIn ? 0 : a.checkedIn ? 1 : -1))
})

// 过滤后的学生列表（兼容原有代码）
const filteredStudents = computed(() => studentListWithCheckin.value)

// REVIEW-P1: 预计算分组，避免模板重复 filter
const notCheckedInStudents = computed(() => 
  studentListWithCheckin.value.filter(s => !s.checkedIn)
)

const checkedInStudents = computed(() => 
  studentListWithCheckin.value.filter(s => s.checkedIn)
)

// 签到统计
const checkinStats = computed(() => {
  if (!classStudents.value) return { total: 0, checkedIn: 0, notCheckedIn: 0 }
  const total = classStudents.value.length
  const checkedIn = classStudents.value.filter(s => checkedInStudentIds.value.has(s.student_id)).length
  return { total, checkedIn, notCheckedIn: total - checkedIn }
})

const handleStartSession = async () => {
  if (!className.value) {
    showErrorToast('请选择班级')
    return
  }

  try {
    await startSession({ className: className.value, courseName: courseName.value || undefined })
    showSuccessToast('课堂已开始！')
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '开始课堂失败')
  }
}

const handleEndSession = async () => {
  try {
    await endSession()
    showSuccessToast('课堂已结束！')
    className.value = ''
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
    // 刷新签到记录
    refetchCheckins()
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '签到失败')
  }
}

// 快速签到
const quickCheckIn = async (studentId: string) => {
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
      <h1 class="text-2xl font-bold text-white">
        课堂签到
      </h1>
      <p class="text-white/60">
        管理您的活跃课堂
      </p>
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
            <p
              v-if="activeSession"
              class="text-sm text-white/60"
            >
              {{ activeSession.class_name }} • 开始于 {{ activeSession.start_time }}
            </p>
            <p
              v-else
              class="text-sm text-white/60"
            >
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
    <Card
      v-if="!isSessionActive"
      class="border-white/10 bg-white/[0.02] p-6"
    >
      <h3 class="font-medium text-white">
        开始新课堂
      </h3>
      <p class="text-sm text-white/60">
        选择课程和班级开始上课
      </p>
      
      <!-- 显示班级占用状态 -->
      <div
        v-if="otherOccupiedClasses.length > 0"
        class="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg"
      >
        <p class="text-sm text-yellow-400 flex items-center gap-2">
          <AlertTriangle class="h-4 w-4" />
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

    <!-- Check-in section -->
    <template v-if="isSessionActive">
      <!-- Check-in form -->
      <Card class="border-white/10 bg-white/[0.02] p-6">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
            <CheckCircle class="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 class="font-medium text-white">
              学生签到
            </h3>
            <p class="text-sm text-white/60">
              输入学生学号进行签到
            </p>
          </div>
        </div>
        <div class="mt-4 flex gap-4">
          <Input
            v-model="studentCode"
            placeholder="请输入学生学号"
            class="flex-1"
            @keyup.enter="handleCheckIn"
          />
          <Button
            :loading="isCheckingIn"
            @click="handleCheckIn"
          >
            <CheckCircle class="mr-2 h-4 w-4" />
            签到
          </Button>
        </div>
      </Card>

      <!-- Stats cards -->
      <div class="grid gap-4 sm:grid-cols-3">
        <Card class="border-white/10 bg-white/[0.02] p-4">
          <div class="flex items-center gap-3">
            <Users class="h-5 w-5 text-white/60" />
            <div>
              <p class="text-xs text-white/50">
                班级人数
              </p>
              <p class="text-xl font-bold text-white">
                {{ checkinStats.total }}
              </p>
            </div>
          </div>
        </Card>
        <Card class="border-white/10 bg-white/[0.02] p-4">
          <div class="flex items-center gap-3">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-green-500/20">
              <CheckCircle class="h-4 w-4 text-green-400" />
            </div>
            <div>
              <p class="text-xs text-white/50">
                已签到
              </p>
              <p class="text-xl font-bold text-green-400">
                {{ checkinStats.checkedIn }}
              </p>
            </div>
          </div>
        </Card>
        <Card class="border-white/10 bg-white/[0.02] p-4">
          <div class="flex items-center gap-3">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-red-500/20">
              <Clock class="h-4 w-4 text-red-400" />
            </div>
            <div>
              <p class="text-xs text-white/50">
                未签到
              </p>
              <p class="text-xl font-bold text-red-400">
                {{ checkinStats.notCheckedIn }}
              </p>
            </div>
          </div>
        </Card>
      </div>

      <!-- Student list - 列表式布局 -->
      <Card class="border-white/10 bg-white/[0.02]">
        <div class="p-4 border-b border-white/10 flex items-center justify-between">
          <div>
            <h3 class="font-medium text-white flex items-center gap-2">
              <GraduationCap class="h-5 w-5" />
              班级学生列表
              <span class="text-sm text-white/50">({{ checkinStats.total }}人)</span>
            </h3>
          </div>
          <div class="relative w-48">
            <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
            <Input
              v-model="searchQuery"
              placeholder="搜索学生..."
              class="pl-10 h-9"
            />
          </div>
        </div>
        
        <div
          v-if="isLoadingStudents"
          class="flex h-48 items-center justify-center"
        >
          <div class="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
        
        <!-- 卡片网格布局 -->
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
              @click="!student.checkedIn && quickCheckIn(student.student_id)"
            >
              <!-- 签到状态图标 -->
              <div 
                class="absolute top-2 right-2 flex h-5 w-5 items-center justify-center rounded-full"
                :class="student.checkedIn ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'"
              >
                <CheckCircle v-if="student.checkedIn" class="h-3 w-3" />
                <span v-else class="text-xs">!</span>
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
                <p class="text-xs text-white/40 mt-0.5">{{ student.student_id }}</p>
                <p v-if="student.checkedIn && student.checkinTime" class="text-xs text-white/50 mt-1">
                  {{ formatTime(student.checkinTime) }}
                </p>
                <p v-else-if="!student.checkedIn" class="text-xs text-red-400/70 mt-1">
                  点击签到
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div
          v-else
          class="flex h-48 flex-col items-center justify-center text-white/60"
        >
          <GraduationCap class="mb-4 h-12 w-12 opacity-50" />
          <p>暂无学生数据</p>
        </div>
      </Card>
    </template>

    <!-- Toast -->
    <Toast
      v-model:show="show"
      :message="toastMessage"
      :variant="toastVariant"
    />
  </div>
</template>
