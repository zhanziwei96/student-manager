import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { classSessionApi, checkinApi } from '@/api'
import type { CheckinRequest, CheckinRecord } from '@/types'

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
  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (data: CheckinRequest): Promise<CheckinRecord> => {
      const res = await checkinApi.checkin(data)
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Check-in failed')
    },
  })

  return { mutateAsync, isPending, error }
}
