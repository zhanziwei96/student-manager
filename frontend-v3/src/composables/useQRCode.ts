import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { get } from '@/lib/api'

const REFRESH_INTERVAL = 15000 // 15秒

export function useVerificationCode(sessionId: number) {
  const expiresIn = ref(15)
  let countdownTimer: ReturnType<typeof setInterval> | null = null

  const { data, refetch, isLoading, error } = useQuery<{ code: string; expires_in: number }>({
    queryKey: ['verification-code', sessionId],
    queryFn: async () => {
      return await get(`/course-sessions/${sessionId}/verification-code`)
    },
    refetchInterval: REFRESH_INTERVAL,
    staleTime: REFRESH_INTERVAL - 1000,
  })

  // 数据刷新时同步重置倒计时，避免 queryFn 副作用
  watch(data, () => {
    expiresIn.value = data.value?.expires_in ?? 15
  }, { immediate: true })

  // 倒计时到 0 时立即触发刷新，避免卡在 0s 等待轮询间隔
  watch(expiresIn, (val) => {
    if (val <= 0) {
      refetch()
    }
  })

  const code = computed(() => {
    if (!data.value) return ''
    return data.value.code as string
  })

  const progressPercent = computed(() => (expiresIn.value / 15) * 100)

  const startCountdown = () => {
    if (countdownTimer) clearInterval(countdownTimer)
    countdownTimer = setInterval(() => {
      if (expiresIn.value > 0) {
        expiresIn.value -= 1
      }
    }, 1000)
  }

  onMounted(startCountdown)
  onUnmounted(() => {
    if (countdownTimer) clearInterval(countdownTimer)
  })

  return { code, expiresIn, progressPercent, isLoading, error, refetch }
}
