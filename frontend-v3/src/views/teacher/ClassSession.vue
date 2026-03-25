<script setup lang="ts">
import { ref, computed } from 'vue'
import { useClassSession, useClassSessionStart, useClassSessionEnd, useStudentCheckIn, useScoreUpdate, useActiveClassSessions } from '@/composables'
import { useClasses, useClassStudents } from '@/composables/useClasses'
import { useTodayCheckins } from '@/composables/useCheckins'
import { Card, Button, Input, Select, Badge, Dialog } from '@/components/ui'
import { Play, Square, CheckCircle, Clock, Users, Search, GraduationCap, Plus, Minus, MessageCircle, AlertTriangle, UserX } from 'lucide-vue-next'
import { Toast } from '@/components/ui'
import type { Student } from '@/types'

const className = ref('')
const studentCode = ref('')
const searchQuery = ref('')

const { data: activeSession } = useClassSession()
const { mutateAsync: startSession, isPending: isStartingSession } = useClassSessionStart()
const { mutateAsync: endSession, isPending: isEndingSession } = useClassSessionEnd()
const { mutateAsync: checkIn, isPending: isCheckingIn } = useStudentCheckIn(computed(() => activeSession.value?.class_name || ''))

// 获取活跃课堂列表
const { data: activeSessions } = useActiveClassSessions()

// 所有被占用的班级列表（用于显示警告）
const occupiedClasses = computed(() => {
  if (!activeSessions.value) return []
  return activeSessions.value
})

// 其他教师占用的班级（排除当前用户的）
const otherOccupiedClasses = computed(() => {
  if (!activeSessions.value) return []
  return activeSessions.value.filter(s => s.class_name !== activeSession.value?.class_name)
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
const { data: classList, isPending: isLoadingClasses } = useClasses()

// 获取选中班级的学生列表
const { data: classStudents, isPending: isLoadingStudents } = useClassStudents(computed(() => activeSession.value?.class_name || ''))

// 获取当前课堂的签到记录
const { data: todayCheckins, refetch: refetchCheckins } = useTodayCheckins(computed(() => activeSession.value?.class_name || ''))

const showToast = ref(false)
const toastMessage = ref('')
const toastVariant = ref<'default' | 'success' | 'error'>('default')

// 分数调整相关
const { mutateAsync: updateScore, isPending: isUpdatingScore } = useScoreUpdate()
const showScoreDialog = ref(false)
const selectedStudent = ref<Student | null>(null)
const scoreChange = ref(0)
const scoreReason = ref('')

// 快速分数选项
const quickScoreOptions = [
  { label: '课堂提问', score: 2, icon: MessageCircle, color: 'text-green-400', bgColor: 'bg-green-500/10', borderColor: 'border-green-500/30' },
  { label: '违反纪律', score: -2, icon: AlertTriangle, color: 'text-orange-400', bgColor: 'bg-orange-500/10', borderColor: 'border-orange-500/30' },
  { label: '旷课', score: -5, icon: UserX, color: 'text-red-400', bgColor: 'bg-red-500/10', borderColor: 'border-red-500/30' },
]

const isSessionActive = computed(() => !!activeSession.value)

// 已签到学生ID集合
const checkedInStudentIds = computed(() => {
  if (!todayCheckins.value) return new Set()
  return new Set(todayCheckins.value.map(c => c.student_id))
})

// 过滤后的学生列表
const filteredStudents = computed(() => {
  if (!classStudents.value) return []
  let students = classStudents.value.map(s => ({
    ...s,
    checkedIn: checkedInStudentIds.value.has(s.student_id)
  }))
  
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

// 签到统计
const checkinStats = computed(() => {
  if (!classStudents.value) return { total: 0, checkedIn: 0, notCheckedIn: 0 }
  const total = classStudents.value.length
  const checkedIn = classStudents.value.filter(s => checkedInStudentIds.value.has(s.student_id)).length
  return { total, checkedIn, notCheckedIn: total - checkedIn }
})

const handleStartSession = async () => {
  if (!className.value) {
    toastMessage.value = '请选择班级'
    toastVariant.value = 'error'
    showToast.value = true
    return
  }

  try {
    await startSession(className.value)
    toastMessage.value = '课堂已开始！'
    toastVariant.value = 'success'
    showToast.value = true
  } catch (err: any) {
    toastMessage.value = err.message || '开始课堂失败'
    toastVariant.value = 'error'
    showToast.value = true
  }
}

const handleEndSession = async () => {
  try {
    await endSession()
    toastMessage.value = '课堂已结束！'
    toastVariant.value = 'success'
    showToast.value = true
    className.value = ''
  } catch (err: any) {
    toastMessage.value = err.message || '结束课堂失败'
    toastVariant.value = 'error'
    showToast.value = true
  }
}

const handleCheckIn = async () => {
  if (!studentCode.value.trim()) {
    toastMessage.value = '请输入学生代码'
    toastVariant.value = 'error'
    showToast.value = true
    return
  }

  try {
    await checkIn(studentCode.value.trim())
    toastMessage.value = '学生签到成功！'
    toastVariant.value = 'success'
    showToast.value = true
    studentCode.value = ''
    // 刷新签到记录
    refetchCheckins()
  } catch (err: any) {
    toastMessage.value = err.message || '签到失败'
    toastVariant.value = 'error'
    showToast.value = true
  }
}

// 快速签到
const quickCheckIn = async (studentId: string) => {
  try {
    await checkIn(studentId)
    toastMessage.value = '签到成功！'
    toastVariant.value = 'success'
    showToast.value = true
    refetchCheckins()
  } catch (err: any) {
    toastMessage.value = err.message || '签到失败'
    toastVariant.value = 'error'
    showToast.value = true
  }
}

// 打开分数调整弹窗
const openScoreDialog = (student: Student, defaultScore: number = 0, defaultReason: string = '') => {
  selectedStudent.value = student
  scoreChange.value = defaultScore
  scoreReason.value = defaultReason
  showScoreDialog.value = true
}

// 处理快速分数调整
const handleQuickScore = async (student: Student, score: number, reason: string) => {
  try {
    await updateScore({
      studentId: student.student_id,
      data: {
        score_change: score,
        reason: reason,
      },
    })
    toastMessage.value = `${student.name} ${score > 0 ? '+' : ''}${score}分`
    toastVariant.value = 'success'
    showToast.value = true
  } catch (err: any) {
    toastMessage.value = err.message || '调整分数失败'
    toastVariant.value = 'error'
    showToast.value = true
  }
}

// 处理自定义分数调整
const handleUpdateScore = async () => {
  if (!selectedStudent.value) return
  try {
    await updateScore({
      studentId: selectedStudent.value.student_id,
      data: {
        score_change: scoreChange.value,
        reason: scoreReason.value,
      },
    })
    toastMessage.value = `${selectedStudent.value.name} 分数已更新`
    toastVariant.value = 'success'
    showToast.value = true
    showScoreDialog.value = false
  } catch (err: any) {
    toastMessage.value = err.message || '更新分数失败'
    toastVariant.value = 'error'
    showToast.value = true
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
            <p v-else class="text-sm text-white/60">选择班级开始新课堂</p>
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
      <p class="text-sm text-white/60">选择您要上课的班级</p>
      
      <!-- 显示班级占用状态 -->
      <div v-if="otherOccupiedClasses.length > 0" class="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
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
      
      <div class="mt-4 flex gap-4">
        <Select 
          v-model="className" 
          class="flex-1"
          placeholder="请选择班级"
          :options="availableClassOptions"
        />
        <Button :loading="isStartingSession" @click="handleStartSession" :disabled="!className">
          <Play class="mr-2 h-4 w-4" />
          开始
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

      <!-- Stats cards -->
      <div class="grid gap-4 sm:grid-cols-3">
        <Card class="border-white/10 bg-white/[0.02] p-4">
          <div class="flex items-center gap-3">
            <Users class="h-5 w-5 text-white/60" />
            <div>
              <p class="text-xs text-white/50">班级人数</p>
              <p class="text-xl font-bold text-white">{{ checkinStats.total }}</p>
            </div>
          </div>
        </Card>
        <Card class="border-white/10 bg-white/[0.02] p-4">
          <div class="flex items-center gap-3">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-green-500/20">
              <CheckCircle class="h-4 w-4 text-green-400" />
            </div>
            <div>
              <p class="text-xs text-white/50">已签到</p>
              <p class="text-xl font-bold text-green-400">{{ checkinStats.checkedIn }}</p>
            </div>
          </div>
        </Card>
        <Card class="border-white/10 bg-white/[0.02] p-4">
          <div class="flex items-center gap-3">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-red-500/20">
              <Clock class="h-4 w-4 text-red-400" />
            </div>
            <div>
              <p class="text-xs text-white/50">未签到</p>
              <p class="text-xl font-bold text-red-400">{{ checkinStats.notCheckedIn }}</p>
            </div>
          </div>
        </Card>
      </div>

      <!-- Student list -->
      <Card class="border-white/10 bg-white/[0.02]">
        <div class="p-4 border-b border-white/10 flex items-center justify-between">
          <div>
            <h3 class="font-medium text-white flex items-center gap-2">
              <GraduationCap class="h-5 w-5" />
              班级学生列表
            </h3>
            <p class="text-sm text-white/50">点击卡片可快速签到，使用下方按钮调整分数</p>
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
        
        <div v-if="isLoadingStudents" class="flex h-48 items-center justify-center">
          <div class="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
        
        <div v-else-if="filteredStudents.length > 0" class="p-4">
          <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <Card
              v-for="student in filteredStudents"
              :key="student.id"
              class="border-white/10 bg-white/[0.02] p-4 hover:bg-white/[0.04] transition-colors"
              :class="student.checkedIn ? 'border-green-500/30' : ''"
            >
              <!-- 学生信息 -->
              <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-3">
                  <div 
                    class="flex h-10 w-10 items-center justify-center rounded-full cursor-pointer"
                    :class="student.checkedIn ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/60 hover:bg-white/20'"
                    @click="!student.checkedIn && quickCheckIn(student.student_id)"
                  >
                    <CheckCircle v-if="student.checkedIn" class="h-5 w-5" />
                    <span v-else class="text-sm">{{ student.name.charAt(0) }}</span>
                  </div>
                  <div>
                    <p class="font-medium text-white">{{ student.name }}</p>
                    <p class="text-xs text-white/50">{{ student.student_id }}</p>
                  </div>
                </div>
                <Badge :variant="student.checkedIn ? 'success' : 'secondary'" class="text-xs">
                  {{ student.checkedIn ? '已签到' : '未签到' }}
                </Badge>
              </div>
              
              <!-- 分数显示 -->
              <div class="mb-3">
                <p class="text-xs text-white/40 mb-1">当前分数</p>
                <p class="text-xl font-bold text-primary">{{ student.score }}</p>
              </div>
              
              <!-- 快速操作按钮 -->
              <div class="grid grid-cols-3 gap-2">
                <Button
                  v-for="option in quickScoreOptions"
                  :key="option.label"
                  size="sm"
                  variant="outline"
                  class="flex flex-col items-center gap-1 h-auto py-2 px-1 text-xs"
                  :class="[option.borderColor, option.color, option.bgColor]"
                  :disabled="isUpdatingScore"
                  @click="handleQuickScore(student, option.score, option.label)"
                >
                  <component :is="option.icon" class="h-3.5 w-3.5" />
                  <span>{{ option.label }}</span>
                  <span :class="option.score > 0 ? 'text-green-400' : 'text-red-400'">
                    {{ option.score > 0 ? '+' : '' }}{{ option.score }}
                  </span>
                </Button>
              </div>
              
              <!-- 自定义分数按钮 -->
              <div class="mt-2 flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  class="flex-1 border-green-500/30 text-green-400 hover:bg-green-500/10"
                  @click="openScoreDialog(student, 5, '加分')"
                >
                  <Plus class="h-3 w-3 mr-1" />
                  加分
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  class="flex-1 border-red-500/30 text-red-400 hover:bg-red-500/10"
                  @click="openScoreDialog(student, -5, '扣分')"
                >
                  <Minus class="h-3 w-3 mr-1" />
                  扣分
                </Button>
              </div>
            </Card>
          </div>
        </div>
        
        <div v-else class="flex h-48 flex-col items-center justify-center text-white/60">
          <GraduationCap class="mb-4 h-12 w-12 opacity-50" />
          <p>暂无学生数据</p>
        </div>
      </Card>
    </template>

    <!-- Toast -->
    <Toast v-model:show="showToast" :message="toastMessage" :variant="toastVariant" />
    
    <!-- Score Dialog -->
    <Dialog v-model:open="showScoreDialog" :title="selectedStudent ? `调整 ${selectedStudent.name} 的分数` : '调整分数'">
      <div class="space-y-4">
        <div class="space-y-2">
          <label class="text-sm text-white/60">分数变化</label>
          <Input
            v-model.number="scoreChange"
            type="number"
            placeholder="输入分数（正数加分，负数扣分）"
          />
        </div>
        <div class="space-y-2">
          <label class="text-sm text-white/60">原因</label>
          <Input
            v-model="scoreReason"
            placeholder="输入分数调整原因"
          />
        </div>
      </div>
      <template #footer>
        <Button variant="outline" @click="showScoreDialog = false">取消</Button>
        <Button
          :loading="isUpdatingScore"
          @click="handleUpdateScore"
        >
          确认调整
        </Button>
      </template>
    </Dialog>
  </div>
</template>
