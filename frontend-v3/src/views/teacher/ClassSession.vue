<script setup lang="ts">
import { ref, computed } from 'vue'
import { useClassSession, useClassSessionStart, useClassSessionEnd, useStudentCheckIn } from '@/composables'
import { Card, Button, Input } from '@/components/ui'
import { Play, Square, CheckCircle, Clock, Users } from 'lucide-vue-next'
import { Toast } from '@/components/ui'

const className = ref('')
const studentCode = ref('')

const { data: activeSession } = useClassSession()
const { mutateAsync: startSession, isPending: isStartingSession } = useClassSessionStart()
const { mutateAsync: endSession, isPending: isEndingSession } = useClassSessionEnd()
const { mutateAsync: checkIn, isPending: isCheckingIn } = useStudentCheckIn()

const showToast = ref(false)
const toastMessage = ref('')
const toastVariant = ref<'default' | 'success' | 'error'>('default')

const isSessionActive = computed(() => !!activeSession.value)

const handleStartSession = async () => {
  if (!className.value.trim()) {
    toastMessage.value = '请输入班级名称'
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
    await checkIn({
      student_code: studentCode.value,
      session_id: activeSession.value?.id || '',
    })
    toastMessage.value = '学生签到成功！'
    toastVariant.value = 'success'
    showToast.value = true
    studentCode.value = ''
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
            <p v-else class="text-sm text-white/60">开始新课堂以进行签到</p>
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
      <p class="text-sm text-white/60">输入班级信息以开始</p>
      <div class="mt-4 flex gap-4">
        <Input
          v-model="className"
          placeholder="请输入班级名称（如：计算机101）"
          class="flex-1"
          @keyup.enter="handleStartSession"
        />
        <Button :loading="isStartingSession" @click="handleStartSession">
          <Play class="mr-2 h-4 w-4" />
          开始
        </Button>
      </div>
    </Card>

    <!-- Check-in form -->
    <Card v-if="isSessionActive" class="border-white/10 bg-white/[0.02] p-6">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
          <CheckCircle class="h-5 w-5 text-primary" />
        </div>
        <div>
          <h3 class="font-medium text-white">学生签到</h3>
          <p class="text-sm text-white/60">输入学生代码进行签到</p>
        </div>
      </div>
      <div class="mt-4 flex gap-4">
        <Input
          v-model="studentCode"
          placeholder="请输入学生代码"
          class="flex-1"
          @keyup.enter="handleCheckIn"
        />
        <Button :loading="isCheckingIn" @click="handleCheckIn">
          <CheckCircle class="mr-2 h-4 w-4" />
          签到
        </Button>
      </div>
    </Card>

    <!-- Session stats -->
    <div v-if="isSessionActive" class="grid gap-6 sm:grid-cols-2">
      <Card class="border-white/10 bg-white/[0.02] p-6">
        <div class="flex items-center gap-3">
          <Users class="h-5 w-5 text-white/60" />
          <div>
            <p class="text-sm text-white/60">已签到</p>
            <p class="text-2xl font-bold text-white">{{ activeSession?.checked_in_count || 0 }}</p>
          </div>
        </div>
      </Card>
      <Card class="border-white/10 bg-white/[0.02] p-6">
        <div class="flex items-center gap-3">
          <Clock class="h-5 w-5 text-white/60" />
          <div>
            <p class="text-sm text-white/60">已进行</p>
            <p class="text-2xl font-bold text-white">45 分钟</p>
          </div>
        </div>
      </Card>
    </div>

    <!-- Toast -->
    <Toast v-model:show="showToast" :message="toastMessage" :variant="toastVariant" />
  </div>
</template>
