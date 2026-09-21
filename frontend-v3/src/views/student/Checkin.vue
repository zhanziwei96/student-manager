<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useStudentProfile } from '@/composables/useStudentProfile'
import { useStudentCourseSession, useStudentSelfCheckin, useHasCheckedInSession } from '@/composables/useStudentCheckin'
import { Card, Button, Badge, DataContainer, Input } from '@/components/ui'
import { useToast } from '@/composables/useToast'
import { CheckCircle, Clock, User, GraduationCap, Loader2, AlertCircle, CalendarCheck, Keyboard } from 'lucide-vue-next'

const { data: studentProfile, isPending: isLoadingProfile } = useStudentProfile()
const { data: classSession, isPending: isLoadingSession, error: sessionError, refetch: refetchSession, hasActiveSession } = useStudentCourseSession(
  computed(() => studentProfile.value?.class_id ?? undefined)
)
const { mutateAsync: doCheckin, isPending: isCheckingIn, error: checkinError } = useStudentSelfCheckin()
const { hasCheckedIn, sessionCheckin, isPending: isLoadingCheckinStatus } = useHasCheckedInSession(computed(() => classSession.value?.id))

const { success: showSuccessToast, error: showErrorToast } = useToast()

const verificationCode = ref('')

const isPageLoading = computed(() => isLoadingProfile.value || isLoadingSession.value || isLoadingCheckinStatus.value)

// 只有「首次加载失败、拿不到任何课堂数据」才算致命错误。
// 课堂状态每 10 秒轮询一次，偶发失败（网络抖动/后端重启）时 TanStack Query 会保留旧数据、
// 同时把 error 置上——此时若按错误态渲染，就会把学生正在输入验证码的输入框整个卸载、光标丢失。
const sessionLoadFailed = computed(() => !!sessionError.value && !classSession.value)

const canCheckin = computed(() => {
  return hasActiveSession.value && !hasCheckedIn.value && !isCheckingIn.value
})

// 是否显示已签到状态（必须有活跃课堂且已签到）
const showCheckedInStatus = computed(() => {
  return hasActiveSession.value && hasCheckedIn.value
})

// 将原始错误转换为用户友好的消息
const friendlyErrorMessage = computed(() => {
  const err = checkinError.value || sessionError.value
  if (!err) return null
  const msg = (err as Error).message || ''
  if (msg.includes('Network Error') || msg.includes('fetch') || msg.includes('Failed to fetch')) {
    return '网络连接异常，请检查网络后重试'
  }
  if (msg.includes('timeout') || msg.includes('超时')) {
    return '请求超时，请稍后重试'
  }
  if (msg.includes('500') || msg.includes('Internal Server Error')) {
    return '服务器繁忙，请稍后重试'
  }
  return msg
})

// 监听错误并弹出 Toast（只弹一次，避免重复）
watch(friendlyErrorMessage, (msg) => {
  if (msg && !sessionLoadFailed.value) {
    // 查询错误已在 DataContainer 中显示，不再弹 Toast
    // mutation 错误才弹 Toast
    if (checkinError.value) {
      showErrorToast(msg, 3000)
    }
  }
}, { flush: 'post' })

const handleCheckin = async () => {
  const code = verificationCode.value.trim().toUpperCase()
  if (!code) {
    showErrorToast('请输入验证码')
    return
  }
  if (code.length !== 6) {
    showErrorToast('验证码为6位字符')
    return
  }

  try {
    await doCheckin(code)
    verificationCode.value = ''
    showSuccessToast('签到成功！')
  } catch (err: any) {
    showErrorToast(err.message || '签到失败，请重试')
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
  <div>
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-medium text-black">
        课堂签到
      </h1>
      <p class="text-[#737373]">
        签到获取课堂积分
      </p>
    </div>

    <!-- Loading State -->
    <div
      v-if="isPageLoading && !sessionLoadFailed"
      class="flex h-64 items-center justify-center"
    >
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
    </div>

    <!-- Page Content -->
    <DataContainer
      v-else-if="sessionError && !studentProfile"
      :error="sessionError"
      empty-text="暂无数据"
      :has-data="false"
      loading-height="16rem"
      @retry="refetchSession"
    />

    <template v-else-if="studentProfile">
      <!-- Student Info Card - Indigo 主题 -->
      <Card
        class="relative overflow-hidden p-4 md:p-6 mb-5"
        :class="'bg-white border-[#e5e5e5]'"
      >
        <div class="flex items-center gap-3 md:gap-4 relative z-10">
          <div
            class="flex h-10 w-10 md:h-12 md:w-12 items-center justify-center rounded-full flex-shrink-0"
            :class="'bg-primary/10 text-primary'"
          >
            <User class="h-5 w-5 md:h-6 md:w-6 text-primary" />
          </div>
          <div class="min-w-0 flex-1">
            <h2 class="font-medium text-black truncate">
              {{ studentProfile.name }}
            </h2>
            <div class="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 text-sm text-[#737373]">
              <span class="flex items-center gap-1">
                <GraduationCap class="h-4 w-4 flex-shrink-0" />
                <span class="truncate">{{ studentProfile.class_name }}</span>
              </span>
              <span class="hidden sm:inline">·</span>
              <span>学号: {{ studentProfile.student_id }}</span>
            </div>
          </div>
        </div>
      </Card>

      <!-- Checkin Status Card - 动态主题 -->
      <Card
        :class="hasActiveSession ? 'bg-green-50 border-green-200' : 'bg-[#fafafa] border-[#e5e5e5]'"
        class="relative overflow-hidden p-4 md:p-6 mb-5"
      >
        <!-- 查询错误状态（仅首次加载就失败、没有可用课堂数据时；后台轮询失败不推翻界面） -->
        <div
          v-if="sessionLoadFailed"
          class="flex items-center gap-3 text-red-500"
        >
          <AlertCircle class="h-5 w-5 flex-shrink-0" />
          <div class="flex-1 min-w-0">
            <p class="font-medium">
              加载课堂信息失败
            </p>
            <p class="text-sm opacity-80">
              {{ friendlyErrorMessage }}
            </p>
          </div>
          <Button
            size="sm"
            variant="outline"
            class="border-red-200 text-red-500 hover:bg-red-50"
            @click="refetchSession"
          >
            重试
          </Button>
        </div>

        <!-- 正常状态 -->
        <div
          v-else
          class="flex items-center gap-3 md:gap-4 relative z-10"
        >
          <div
            :class="hasActiveSession ? 'bg-green-100 text-green-600' : 'bg-[#f5f5f5] text-[#525252]'"
            class="flex h-10 w-10 md:h-12 md:w-12 items-center justify-center rounded-full flex-shrink-0"
          >
            <Clock
              v-if="!hasActiveSession"
              class="h-5 w-5 md:h-6 md:w-6"
            />
            <CheckCircle
              v-else
              class="h-5 w-5 md:h-6 md:w-6"
            />
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="font-medium text-black">
              {{ hasActiveSession ? '课堂进行中' : '暂无活跃课堂' }}
            </h2>
            <p
              v-if="hasActiveSession && classSession"
              class="text-sm text-[#737373] truncate"
            >
              {{ classSession.teacher_name || '教师' }} 老师正在上课
              <span v-if="classSession.start_time" class="hidden sm:inline">· 已开始 {{ formatTime(classSession.start_time) }}</span>
            </p>
            <p
              v-else
              class="text-sm text-[#737373]"
            >
              请等待老师开启课堂后进行签到
            </p>
          </div>
          <Badge
            v-if="showCheckedInStatus"
            variant="success"
            class="flex-shrink-0 border-0 bg-green-100 text-green-600"
          >
            <CalendarCheck class="mr-1 h-3 w-3" />
            已签到
          </Badge>
        </div>

        <!-- Checkin Verification Code - 背景区域
             注意：这里只看 hasActiveSession，不能加 !sessionError——
             轮询偶发失败会把学生正在输入的验证码框卸载、光标丢失 -->
        <div
          v-if="hasActiveSession"
          class="mt-4 md:mt-6 p-4 rounded-xl border border-green-500/20"
        >
          <div
            v-if="canCheckin && !isCheckingIn"
            class="flex flex-col items-center gap-4"
          >
            <div class="flex h-14 w-14 items-center justify-center rounded-full bg-[#e0e7ff]">
              <Keyboard class="h-7 w-7 text-[#6366f1]" />
            </div>
            <h3 class="text-base font-medium text-[#171717]">输入验证码签到</h3>
            <Input
              v-model="verificationCode"
              placeholder="请输入6位验证码"
              maxlength="6"
              class="w-full max-w-[200px] text-center text-xl tracking-[0.15em] uppercase"
              @keyup.enter="handleCheckin"
            />
            <Button variant="cta" class="h-14 w-full max-w-[200px] text-base" @click="handleCheckin">
              <CheckCircle class="h-4 w-4" />
              确认签到
            </Button>
          </div>

          <div
            v-if="isCheckingIn"
            class="flex flex-col items-center justify-center gap-3 py-8"
          >
            <Loader2 class="h-8 w-8 animate-spin text-primary" />
            <p class="text-sm text-[#737373]">
              正在签到，请稍候...
            </p>
          </div>

          <div
            v-else-if="showCheckedInStatus && sessionCheckin"
            class="rounded-lg border border-green-500/20 bg-green-500/10 p-4 md:p-6 text-center"
          >
            <CheckCircle class="mx-auto h-8 w-8 md:h-10 md:w-10 text-green-400" />
            <p class="mt-2 text-green-400 font-medium text-base md:text-lg">
              本节课已完成签到
            </p>
            <p class="text-sm text-[#737373] mt-1">
              签到时间: {{ new Date(sessionCheckin.checkin_time).toLocaleString() }}
            </p>
          </div>
        </div>

        <!-- Error Message -->
        <div
          v-if="checkinError"
          class="mt-4 rounded-lg border border-red-500/20 bg-red-500/10 p-3"
        >
          <div class="flex items-center gap-2 text-red-400">
            <AlertCircle class="h-4 w-4 flex-shrink-0" />
            <span class="text-sm">{{ friendlyErrorMessage }}</span>
          </div>
        </div>
      </Card>

      <!-- Checkin Tips - Indigo 主题 -->
      <Card
        class="relative overflow-hidden p-4 md:p-6"
        :class="'bg-white border-[#e5e5e5]'"
      >
        <div class="relative z-10">
          <h3 class="font-medium text-black mb-4 text-base md:text-lg">
            签到说明
          </h3>
          <ul class="space-y-3 md:space-y-4 text-sm text-primary">
            <li class="flex items-start gap-3">
              <div
                class="h-6 w-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                :class="'bg-primary/10 text-primary'"
              >
                <span class="text-xs font-medium text-primary">1</span>
              </div>
              <span class="leading-relaxed text-[#737373]">请在老师开启课堂后进行签到</span>
            </li>
            <li class="flex items-start gap-3">
              <div
                class="h-6 w-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                :class="'bg-primary/10 text-primary'"
              >
                <span class="text-xs font-medium text-primary">2</span>
              </div>
              <span class="leading-relaxed text-[#737373]">每节课只能签到一次，不可重复签到</span>
            </li>
            <li class="flex items-start gap-3">
              <div
                class="h-6 w-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                :class="'bg-primary/10 text-primary'"
              >
                <span class="text-xs font-medium text-primary">3</span>
              </div>
              <span class="leading-relaxed text-[#737373]">签到可获得课堂参与积分</span>
            </li>
          </ul>
        </div>
      </Card>
    </template>
  </div>
</template>
