<script setup lang="ts">
import { ref, computed } from 'vue'
import { useStudentProfile } from '@/composables/useStudentProfile'
import { useStudentClassSession, useStudentSelfCheckin, useHasCheckedInSession } from '@/composables/useStudentCheckin'
import { Card, Button, Badge } from '@/components/ui'
import { CheckCircle, Clock, User, GraduationCap, Loader2, AlertCircle, CalendarCheck } from 'lucide-vue-next'
const { data: studentProfile, isPending: isLoadingProfile } = useStudentProfile()
const { data: classSession, isPending: isLoadingSession, hasActiveSession } = useStudentClassSession()
const { mutateAsync: doCheckin, isPending: isCheckingIn, error: checkinError } = useStudentSelfCheckin()
const { hasCheckedIn, sessionCheckin } = useHasCheckedInSession(computed(() => classSession.value?.id))

const showSuccessToast = ref(false)
const successMessage = ref('')

const canCheckin = computed(() => {
  return hasActiveSession.value && !hasCheckedIn.value
})

// 是否显示已签到状态（必须有活跃课堂且已签到）
const showCheckedInStatus = computed(() => {
  return hasActiveSession.value && hasCheckedIn.value
})

const handleCheckin = async () => {
  try {
    await doCheckin()
    showSuccessToast.value = true
    successMessage.value = '签到成功！'
    setTimeout(() => {
      showSuccessToast.value = false
    }, 3000)
  } catch (err: any) {
    // 错误由 mutation 处理
  }
}

const formatTime = (time: string) => {
  try {
    return new Date(time).toLocaleString('zh-CN')
  } catch {
    return time
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">课堂签到</h1>
      <p class="text-white/60">签到获取课堂积分</p>
    </div>

    <!-- Loading State -->
    <div v-if="isLoadingProfile || isLoadingSession" class="flex h-64 items-center justify-center">
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Student Info Card -->
    <Card v-else-if="studentProfile" class="border-white/10 bg-white/[0.02] p-6">
      <div class="flex items-center gap-4">
        <div class="flex h-12 w-12 items-center justify-center rounded-full bg-primary/20">
          <User class="h-6 w-6 text-primary" />
        </div>
        <div>
          <h2 class="font-medium text-white">{{ studentProfile.name }}</h2>
          <div class="flex items-center gap-3 text-sm text-white/60">
            <span class="flex items-center gap-1">
              <GraduationCap class="h-4 w-4" />
              {{ studentProfile.class_name }}
            </span>
            <span>学号: {{ studentProfile.student_id }}</span>
          </div>
        </div>
      </div>
    </Card>

    <!-- Checkin Status Card -->
    <Card 
      class="border-white/10 p-6"
      :class="hasActiveSession ? 'bg-green-500/5 border-green-500/20' : 'bg-white/[0.02]'"
    >
      <div class="flex items-center gap-4">
        <div 
          class="flex h-12 w-12 items-center justify-center rounded-full"
          :class="hasActiveSession ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/60'"
        >
          <Clock v-if="!hasActiveSession" class="h-6 w-6" />
          <CheckCircle v-else class="h-6 w-6" />
        </div>
        <div class="flex-1">
          <h2 class="font-medium text-white">
            {{ hasActiveSession ? '课堂进行中' : '暂无活跃课堂' }}
          </h2>
          <p v-if="hasActiveSession && classSession" class="text-sm text-white/60">
            {{ classSession.teacher_name || '教师' }} 老师正在上课
            <span v-if="classSession.start_time">· 已开始 {{ formatTime(classSession.start_time) }}</span>
          </p>
          <p v-else class="text-sm text-white/60">
            请等待老师开启课堂后进行签到
          </p>
        </div>
        <Badge 
          v-if="showCheckedInStatus" 
          variant="success"
          class="bg-green-500/20 text-green-400 border-green-500/30"
        >
          <CalendarCheck class="mr-1 h-3 w-3" />
          已签到
        </Badge>
      </div>

      <!-- Checkin Button -->
      <div v-if="hasActiveSession" class="mt-6">
        <Button
          v-if="canCheckin"
          size="lg"
          class="w-full"
          :loading="isCheckingIn"
          @click="handleCheckin"
        >
          <CheckCircle class="mr-2 h-5 w-5" />
          立即签到
        </Button>
        
        <div 
          v-else-if="showCheckedInStatus && sessionCheckin" 
          class="rounded-lg border border-green-500/20 bg-green-500/10 p-4 text-center"
        >
          <CheckCircle class="mx-auto h-8 w-8 text-green-400" />
          <p class="mt-2 text-green-400 font-medium">本节课已完成签到</p>
          <p class="text-sm text-white/60">
            签到时间: {{ new Date(sessionCheckin.checkin_time).toLocaleString() }}
          </p>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="checkinError" class="mt-4 rounded-lg border border-red-500/20 bg-red-500/10 p-3">
        <div class="flex items-center gap-2 text-red-400">
          <AlertCircle class="h-4 w-4" />
          <span class="text-sm">{{ (checkinError as Error).message }}</span>
        </div>
      </div>
    </Card>

    <!-- Checkin Tips -->
    <Card class="border-white/10 bg-white/[0.02] p-6">
      <h3 class="font-medium text-white mb-4">签到说明</h3>
      <ul class="space-y-3 text-sm text-white/60">
        <li class="flex items-start gap-2">
          <div class="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
            <span class="text-xs text-primary">1</span>
          </div>
          <span>请在老师开启课堂后进行签到</span>
        </li>
        <li class="flex items-start gap-2">
          <div class="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
            <span class="text-xs text-primary">2</span>
          </div>
          <span>每节课只能签到一次，不可重复签到</span>
        </li>
        <li class="flex items-start gap-2">
          <div class="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
            <span class="text-xs text-primary">3</span>
          </div>
          <span>签到可获得课堂参与积分</span>
        </li>
      </ul>
    </Card>

    <!-- Success Toast -->
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="transform translate-y-2 opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="transform translate-y-0 opacity-100"
      leave-to-class="transform translate-y-2 opacity-0"
    >
      <div
        v-if="showSuccessToast"
        class="fixed bottom-4 right-4 z-50 rounded-lg border border-green-500/20 bg-green-500/10 px-4 py-3 shadow-lg"
      >
        <div class="flex items-center gap-2 text-green-400">
          <CheckCircle class="h-5 w-5" />
          <span>{{ successMessage }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>
