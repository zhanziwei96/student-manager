import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { api } from '@/lib/api'

const REFRESH_INTERVAL = 10000 // 10秒

export function useQRCode(sessionId: number) {
  const expiresIn = ref(10)
  let countdownTimer: ReturnType<typeof setInterval> | null = null

  const { data, refetch, isLoading, error } = useQuery({
    queryKey: ['qr-payload', sessionId],
    queryFn: async () => {
      const res = await api.get(`/course-sessions/${sessionId}/qr-payload`)
      expiresIn.value = 10
      return res.data.data
    },
    refetchInterval: REFRESH_INTERVAL,
    staleTime: REFRESH_INTERVAL,
  })

  const qrContent = computed(() => {
    if (!data.value) return ''
    return JSON.stringify(data.value)
  })

  const progressPercent = computed(() => (expiresIn.value / 10) * 100)

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

  return { qrContent, expiresIn, progressPercent, isLoading, error, refetch }
}
