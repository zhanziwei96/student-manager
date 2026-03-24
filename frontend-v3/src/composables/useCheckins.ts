import { useQuery } from '@tanstack/vue-query'
import { checkinApi } from '@/api/checkin'
import type { CheckinRecord } from '@/types'

/**
 * 获取今日签到统计
 */
export function useCheckinStats() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['checkin-stats'],
    queryFn: async () => {
      const res = await checkinApi.getStats()
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch checkin stats')
    },
    refetchInterval: 30000, // 每30秒刷新一次
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}

/**
 * 获取今日签到列表
 */
export function useTodayCheckins(className?: string) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['today-checkins', className],
    queryFn: async () => {
      const res = await checkinApi.getToday(className)
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch today checkins')
    },
    refetchInterval: 30000, // 每30秒刷新一次
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}
