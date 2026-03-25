import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { unref, type Ref } from 'vue'
import { classSessionApi, checkinApi } from '@/api'
import type { CheckinRecord } from '@/types'

/**
 * Class Session composable - FE-003 修复后
 * 使用统一的 API 响应处理，无需手动检查 res.success
 */
export function useClassSession() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['classSession'],
    queryFn: async () => {
      // FE-003: 直接获取数据，错误自动抛出
      const data = await classSessionApi.getCurrent()
      if (data?.active) {
        // 同步到 localStorage
        localStorage.setItem('activeClassSession', JSON.stringify(data))
        return data
      }

      // 服务器没有活跃课堂，清除 localStorage
      localStorage.removeItem('activeClassSession')
      return null
    },
    staleTime: 5000,
    refetchOnWindowFocus: true,
  })

  return { data, isPending, error, refetch }
}

export function useClassSessionStart() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (className: string) => {
      // FE-003: 直接获取数据，错误自动抛出
      const data = await classSessionApi.start({ class_name: className })
      localStorage.setItem('activeClassSession', JSON.stringify(data))
      return data
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['classSession'], data)
    },
  })

  return { mutateAsync, isPending, error }
}

export function useClassSessionEnd() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async () => {
      // FE-003: 直接调用，错误自动抛出
      await classSessionApi.end()
      localStorage.removeItem('activeClassSession')
    },
    onSuccess: () => {
      queryClient.setQueryData(['classSession'], null)
      queryClient.invalidateQueries({ queryKey: ['students'] })
      queryClient.invalidateQueries({ queryKey: ['today-checkins'] })
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
    },
  })

  return { mutateAsync, isPending, error }
}

/**
 * 获取所有活跃课堂列表
 */
export function useActiveClassSessions() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['active-class-sessions'],
    queryFn: async () => {
      // FE-003: 直接获取数据，错误自动抛出
      return await classSessionApi.getActiveSessions()
    },
    refetchInterval: 10000,
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}

export function useStudentCheckIn(className?: string | Ref<string>) {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (studentCode: string): Promise<CheckinRecord> => {
      // FE-003: 直接获取数据，错误自动抛出
      return await checkinApi.checkin({
        student_id: studentCode,
        student_name: '',
      })
    },
    onSuccess: () => {
      const resolvedClassName = unref(className)
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
      if (resolvedClassName) {
        queryClient.invalidateQueries({ queryKey: ['today-checkins', resolvedClassName] })
      } else {
        queryClient.invalidateQueries({ queryKey: ['today-checkins'] })
      }
    },
  })

  return { mutateAsync, isPending, error }
}
