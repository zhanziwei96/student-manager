import { useQuery } from '@tanstack/vue-query'
import { toValue, type Ref } from 'vue'
import { checkinApi } from '@/api/checkin'

/**
 * 获取签到统计（按 session）- FE-003 修复后
 */
export function useSessionCheckinStats(sessionId?: number | Ref<number | undefined>) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['checkin-stats', toValue(sessionId)],
    queryFn: async () => {
      const id = toValue(sessionId)
      return await checkinApi.getStats(id)
    },
    refetchInterval: 10000,
    enabled: () => toValue(sessionId) !== undefined,
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}

/**
 * 获取指定课堂的签到列表 - 按 session 维度
 */
export function useSessionCheckins(sessionId?: number | Ref<number | undefined>) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['session-checkins', toValue(sessionId)],
    queryFn: async () => {
      const id = toValue(sessionId)
      if (id === undefined) return []
      return await checkinApi.getSessionCheckins(id)
    },
    refetchInterval: 10000,
    enabled: () => toValue(sessionId) !== undefined,
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}

