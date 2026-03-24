import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { classSessionApi, checkinApi } from '@/api'
import type { CheckinRecord } from '@/types'

/**
 * Class Session composable
 * Based on: https://github.com/tanstack/query
 */
export function useClassSession() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['classSession'],
    queryFn: async () => {
      // 优先从 localStorage 获取
      const stored = localStorage.getItem('activeClassSession')
      if (stored) {
        return JSON.parse(stored)
      }
      return null
    },
    staleTime: Infinity, // Never stale - manage manually
  })

  return { data, isPending, error, refetch }
}

export function useClassSessionStart() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (className: string) => {
      const res = await classSessionApi.start({ class_name: className })
      if (res.success && res.data) {
        localStorage.setItem('activeClassSession', JSON.stringify(res.data))
        return res.data
      }
      throw new Error(res.message || 'Failed to start class')
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
      const res = await classSessionApi.end()
      if (!res.success) {
        throw new Error(res.message || 'Failed to end class')
      }
      localStorage.removeItem('activeClassSession')
    },
    onSuccess: () => {
      queryClient.setQueryData(['classSession'], null)
    },
  })

  return { mutateAsync, isPending, error }
}

export function useStudentCheckIn() {
  const queryClient = useQueryClient()
  
  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (studentCode: string): Promise<CheckinRecord> => {
      // 直接调用签到API，后端会验证学生存在性
      const res = await checkinApi.checkin({
        student_id: studentCode,
        student_name: '', // 后端会根据student_id查找
      })
      
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || '签到失败')
    },
    onSuccess: () => {
      // 刷新签到统计
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
      queryClient.invalidateQueries({ queryKey: ['today-checkins'] })
    },
  })

  return { mutateAsync, isPending, error }
}
