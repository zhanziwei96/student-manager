import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { classSessionApi } from '@/api'
import type { CheckInRequest, CheckInResponse } from '@/types'

/**
 * Class Session composable
 * Based on: https://github.com/tanstack/query
 */
export function useClassSession() {
  return useQuery({
    queryKey: ['classSession'],
    queryFn: async () => {
      // Try to get from localStorage first
      const stored = localStorage.getItem('activeClassSession')
      if (stored) {
        return JSON.parse(stored)
      }
      return null
    },
    staleTime: Infinity, // Never stale - manage manually
  })
}

export function useStartClassSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (className: string) => {
      const res = await classSessionApi.start(className)
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
}

export function useEndClassSession() {
  const queryClient = useQueryClient()

  return useMutation({
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
}

export function useCheckIn() {
  return useMutation({
    mutationFn: async (data: CheckInRequest): Promise<CheckInResponse> => {
      const res = await classSessionApi.checkIn(data)
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Check-in failed')
    },
  })
}
