import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, type Ref, ref } from 'vue'
import { checkinApi } from '@/api/checkin'
import { useStudentProfile } from './useStudentProfile'
import { useSessionCheckins } from './useCheckins'
import { getDeviceFingerprint, getDeviceInfo } from '@/lib/device'
import type { CheckinRecord } from '@/types'

/**
 * 学生签到 - 获取所在班级的活跃课堂状态 - FE-003 修复后
 */
export function useStudentCourseSession(className?: string | Ref<string>) {
  const { data: studentProfile } = useStudentProfile()

  const targetClassName = computed(() => {
    if (className) return typeof className === 'string' ? className : className.value
    return studentProfile.value?.class_name
  })

  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['student-course-session', targetClassName],
    queryFn: async () => {
      const classNameValue = targetClassName.value
      if (!classNameValue) return null

      // FE-003: 直接获取数据，错误自动抛出
      return await checkinApi.getCourseSessionForClass(classNameValue)
    },
    enabled: computed(() => !!targetClassName.value),
    staleTime: 5000, // 5秒内不重复请求，避免组件快速切换时堆积
    refetchInterval: 10000,
    refetchOnWindowFocus: false, // 签到页面不需要窗口聚焦时刷新
  })

  return {
    data,
    isPending,
    error,
    refetch,
    className: targetClassName,
    hasActiveSession: computed(() => data.value?.active || false),
  }
}

/**
 * 学生签到 - 执行签到 - FE-003 修复后
 */
export function useStudentSelfCheckin() {
  const queryClient = useQueryClient()
  const { data: studentProfile } = useStudentProfile()

  const { mutateAsync, isPending, error, isSuccess } = useMutation({
    mutationFn: async (): Promise<CheckinRecord> => {
      if (!studentProfile.value) {
        throw new Error('未找到学生信息')
      }

      // 获取设备指纹
      const deviceId = await getDeviceFingerprint()
      const deviceInfo = JSON.stringify(getDeviceInfo())

      // FE-003: 直接获取数据，错误自动抛出
      return await checkinApi.checkin({
        student_id: studentProfile.value.student_id,
        student_name: studentProfile.value.name,
        device_id: deviceId,
        device_info: deviceInfo,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-course-session'] })
      // 使用 exact: false 匹配所有以 ['session-checkins'] 开头的 query（包含 sessionId）
      queryClient.invalidateQueries({ queryKey: ['session-checkins'], exact: false })
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
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
 */
export function useHasCheckedInSession(sessionId?: number | Ref<number | undefined>) {
  const { data: studentProfile } = useStudentProfile()
  const { data: sessionCheckins, isPending } = useSessionCheckins(sessionId)

  const targetSessionId = computed(() => {
    if (sessionId === undefined) return undefined
    return typeof sessionId === 'number' ? sessionId : sessionId.value
  })

  const hasCheckedIn = computed(() => {
    if (!sessionCheckins.value || !studentProfile.value || !targetSessionId.value) return false
    return sessionCheckins.value.some(
      c => c.student_id === studentProfile.value!.student_id && c.session_id === targetSessionId.value
    )
  })

  const sessionCheckin = computed(() => {
    if (!sessionCheckins.value || !studentProfile.value || !targetSessionId.value) return null
    return sessionCheckins.value.find(
      c => c.student_id === studentProfile.value!.student_id && c.session_id === targetSessionId.value
    ) || null
  })

  return {
    hasCheckedIn,
    sessionCheckin,
    isPending,
  }
}
