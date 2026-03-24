<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useClassSession, useClassSessionStart, useClassSessionEnd, useStudentCheckIn } from '@/composables'
import { useClasses, useClassStudents } from '@/composables/useClasses'
import { useTodayCheckins } from '@/composables/useCheckins'
import { Card, Button, Input, Select } from '@/components/ui'
import { Play, Square, CheckCircle, Clock, Users, Search, GraduationCap } from 'lucide-vue-next'
import { Toast } from '@/components/ui'

const className = ref('')
const studentCode = ref('')
const searchQuery = ref('')

const { data: activeSession } = useClassSession()
const { mutateAsync: startSession, isPending: isStartingSession } = useClassSessionStart()
const { mutateAsync: endSession, isPending: isEndingSession } = useClassSessionEnd()
const { mutateAsync: checkIn, isPending: isCheckingIn } = useStudentCheckIn()

// 获取班级列表
const { data: classList, isPending: isLoadingClasses } = useClasses()

// 获取选中班级的学生列表
const { data: classStudents, isPending: isLoadingStudents } = useClassStudents(computed(() => activeSession.value?.class_name || ''))

// 获取今日签到记录
const { data: todayCheckins, refetch: refetchCheckins } = useTodayCheckins()

const showToast = ref(false)
const toastMessage = ref('')
const toastVariant = ref<'default' | 'success' | 'error'>('default')

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
      <div class="mt-4 flex gap-4">
        <Select 
          v-model="className" 
          class="flex-1"
          placeholder="请选择班级"
          :options="(classList || []).map(cls => ({ value: cls, label: cls }))"
        />
        <Button :loading="isStartingSession" @click="handleStartSession">
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
            <p class="text-sm text-white/50">点击未签到学生可快速签到</p>
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
        
        <div v-else-if="filteredStudents.length > 0" class="divide-y divide-white/5">
          <div
            v-for="student in filteredStudents"
            :key="student.id"
            class="flex items-center justify-between p-4 hover:bg-white/5 cursor-pointer transition-colors"
            @click="!student.checkedIn && quickCheckIn(student.student_id)"
          >
            <div class="flex items-center gap-4">
              <div 
                class="flex h-10 w-10 items-center justify-center rounded-full"
                :class="student.checkedIn ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/60'"
              >
                <CheckCircle v-if="student.checkedIn" class="h-5 w-5" />
                <span v-else class="text-sm">{{ student.name.charAt(0) }}</span>
              </div>
              <div>
                <p class="font-medium text-white">{{ student.name }}</p>
                <p class="text-sm text-white/50">{{ student.student_id }}</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <Badge :variant="student.checkedIn ? 'success' : 'secondary'">
                {{ student.checkedIn ? '已签到' : '未签到' }}
              </Badge>
              <Button 
                v-if="!student.checkedIn" 
                size="sm" 
                variant="outline"
                @click.stop="quickCheckIn(student.student_id)"
              >
                签到
              </Button>
            </div>
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
  </div>
</template>
