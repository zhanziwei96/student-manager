import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, type Ref, ref, toValue, type MaybeRefOrGetter } from 'vue'
import { checkinApi } from '@/api/checkin'
import { useStudentProfile } from './useStudentProfile'
import { getEnhancedDeviceFingerprint, getDeviceInfo } from '@/lib/device'
import type { CheckinRecord } from '@/types'

/**
 * 学生签到 - 获取所在班级的活跃课堂状态 - FE-003 修复后
 *
 * Phase 6 起 `/course-sessions/class/{class_id}` 只接受行政班 ID，
 * 由调用方传入学生的 class_id（来自学生详情响应 `class_id` 字段，未分班为 null）。
 */
export function useStudentCourseSession(classId?: MaybeRefOrGetter<number | undefined>) {
  const targetClassId = computed(() => toValue(classId))

  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['student-course-session', targetClassId],
    queryFn: async () => {
      const classIdValue = targetClassId.value
      if (!classIdValue) return null

      // FE-003: 直接获取数据，错误自动抛出
      return await checkinApi.getCourseSessionForClass(classIdValue)
    },
    enabled: computed(() => !!targetClassId.value),
    staleTime: 5000, // 5秒内不重复请求，避免组件快速切换时堆积
    refetchInterval: 10000,
    refetchOnWindowFocus: false, // 签到页面不需要窗口聚焦时刷新
    retry: (failureCount, error) => {
      // 网络错误重试 2 次，业务错误不重试
      const msg = (error as Error).message || ''
      const isNetworkError = msg.includes('Network Error') || msg.includes('fetch') || msg.includes('Failed to fetch')
      return isNetworkError && failureCount < 2
    },
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 3000),
  })

  return {
    data,
    isPending,
    error,
    refetch,
    classId: targetClassId,
    hasActiveSession: computed(() => data.value?.active || false),
  }
}

/**
 * 学生签到 mutation 变量
 *
 * 兼容两种调用形状：
 * - 字符串：仅验证码（原有形状，无座位图课堂）
 * - 对象：验证码 + 座位（座位图课堂，seat_id 与后端 CheckinRequest 字段同名）
 */
export type SelfCheckinVariables = string | { verification_code: string; seat_id?: number }

/**
 * 学生签到 - 执行签到 - FE-003 修复后
 */
export function useStudentSelfCheckin() {
  const queryClient = useQueryClient()
  const { data: studentProfile } = useStudentProfile()

  const { mutateAsync, isPending, error, isSuccess } = useMutation({
    mutationFn: async (variables: SelfCheckinVariables): Promise<CheckinRecord> => {
      if (!studentProfile.value) {
        throw new Error('未找到学生信息')
      }

      const verificationCode = typeof variables === 'string' ? variables : variables.verification_code
      const seatId = typeof variables === 'string' ? undefined : variables.seat_id

      // 获取设备指纹
      const deviceId = await getEnhancedDeviceFingerprint()
      const deviceInfo = JSON.stringify(getDeviceInfo())

      // FE-003: 直接获取数据，错误自动抛出
      return await checkinApi.checkin({
        student_id: studentProfile.value.student_id,
        student_name: studentProfile.value.name,
        device_id: deviceId,
        device_info: deviceInfo,
        verification_code: verificationCode.toUpperCase(),
        ...(seatId != null ? { seat_id: seatId } : {}),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-course-session'] })
      // 立即刷新本人签到状态（签到页据此显示"已签到"）
      queryClient.invalidateQueries({ queryKey: ['my-checkin-status'], exact: false })
      queryClient.invalidateQueries({ queryKey: ['session-checkins'], exact: false })
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
      // 座位图课堂：签到成功后刷新座位占用状态
      queryClient.invalidateQueries({ queryKey: ['seat-map'], exact: false })
    },
    retry: (failureCount, error) => {
      // 网络错误重试 1 次，业务错误（如 409 重复签到）不重试
      const msg = (error as Error).message || ''
      const isNetworkError = msg.includes('Network Error') || msg.includes('fetch') || msg.includes('Failed to fetch')
      return isNetworkError && failureCount < 1
    },
  })

  return {
    mutateAsync,
    isPending,
    error,
    isSuccess,
  }
}

/**
 * 获取GPS定位
 */
export function useGeolocation() {
  const isLocating = ref(false)
  const locationError = ref<string | null>(null)
  const position = ref<{ lat: number; lng: number } | null>(null)

  const getCurrentPosition = (): Promise<{ lat: number; lng: number } | null> => {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        locationError.value = '您的浏览器不支持地理定位'
        resolve(null)
        return
      }

      isLocating.value = true
      locationError.value = null

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          position.value = {
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
          }
          isLocating.value = false
          resolve(position.value)
        },
        (err) => {
          isLocating.value = false
          switch (err.code) {
            case err.PERMISSION_DENIED:
              locationError.value = '请允许访问位置信息以完成签到'
              break
            case err.POSITION_UNAVAILABLE:
              locationError.value = '无法获取位置信息，请检查GPS设置'
              break
            case err.TIMEOUT:
              locationError.value = '获取位置超时，请重试'
              break
            default:
              locationError.value = '定位失败，请重试'
          }
          resolve(null)
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        }
      )
    })
  }

  return {
    isLocating,
    locationError,
    position,
    getCurrentPosition,
  }
}

/**
 * 检查学生是否已在指定课堂签到
 *
 * 使用 GET /checkins/my-status（仅返回本人记录）。
 * 不可用教师接口 /checkins/session/{id}：会返回全班名单且学生无权访问（403）。
 */
export function useHasCheckedInSession(sessionId?: number | Ref<number | undefined>) {
  const targetSessionId = computed(() => {
    if (sessionId === undefined) return undefined
    return typeof sessionId === 'number' ? sessionId : sessionId.value
  })

  const { data, isPending } = useQuery({
    queryKey: computed(() => ['my-checkin-status', targetSessionId.value]),
    queryFn: async () => {
      const id = targetSessionId.value
      if (id === undefined) return null
      return await checkinApi.getMyCheckinStatus(id)
    },
    enabled: computed(() => targetSessionId.value !== undefined),
    refetchInterval: 10000,
    retry: (failureCount, error) => {
      // 网络错误重试 2 次，业务错误不重试
      const msg = (error as Error).message || ''
      const isNetworkError = msg.includes('Network Error') || msg.includes('fetch') || msg.includes('Failed to fetch')
      return isNetworkError && failureCount < 2
    },
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 3000),
  })

  const hasCheckedIn = computed(() => data.value?.checked_in ?? false)

  // 保持与旧返回结构兼容：sessionCheckin 仅暴露签到时间
  const sessionCheckin = computed(() => {
    if (!data.value?.checked_in || !data.value.checkin_time) return null
    return {
      student_id: '',
      session_id: targetSessionId.value ?? 0,
      checkin_time: data.value.checkin_time,
    } as CheckinRecord
  })

  return {
    hasCheckedIn,
    sessionCheckin,
    isPending,
  }
}
