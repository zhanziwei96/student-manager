import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, type Ref } from 'vue'
import { checkinApi } from '@/api/checkin'
import { useStudentProfile } from './useStudentProfile'
import { useTodayCheckins } from './useCheckins'
import type { CheckinRecord } from '@/types'

/**
 * 学生签到 - 获取所在班级的活跃课堂状态 - FE-003 修复后
 */
export function useStudentClassSession(className?: string | Ref<string>) {
  const { data: studentProfile } = useStudentProfile()

  const targetClassName = computed(() => {
    if (className) return typeof className === 'string' ? className : className.value
    return studentProfile.value?.class_name
  })

  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['student-class-session', targetClassName],
    queryFn: async () => {
      const classNameValue = targetClassName.value
      if (!classNameValue) return null

      // FE-003: 直接获取数据，错误自动抛出
      return await checkinApi.getClassSessionForClass(classNameValue)
    },
    enabled: computed(() => !!targetClassName.value),
    refetchInterval: 10000,
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

      // FE-003: 直接获取数据，错误自动抛出
      return await checkinApi.checkin({
        student_id: studentProfile.value.student_id,
        student_name: studentProfile.value.name,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-class-session'] })
      queryClient.invalidateQueries({ queryKey: ['today-checkins'] })
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
 * 检查学生是否已在指定课堂签到
 */
export function useHasCheckedInSession(sessionId?: number | Ref<number | undefined>) {
  const { data: studentProfile } = useStudentProfile()
  const { data: todayCheckins, isPending } = useTodayCheckins()

  const targetSessionId = computed(() => {
    if (sessionId === undefined) return undefined
    return typeof sessionId === 'number' ? sessionId : sessionId.value
  })

  const hasCheckedIn = computed(() => {
    if (!todayCheckins.value || !studentProfile.value || !targetSessionId.value) return false
    return todayCheckins.value.some(
      c => c.student_id === studentProfile.value!.student_id && c.session_id === targetSessionId.value
    )
  })

  const sessionCheckin = computed(() => {
    if (!todayCheckins.value || !studentProfile.value || !targetSessionId.value) return null
    return todayCheckins.value.find(
      c => c.student_id === studentProfile.value!.student_id && c.session_id === targetSessionId.value
    ) || null
  })

  return {
    hasCheckedIn,
    sessionCheckin,
    isPending,
  }
}
