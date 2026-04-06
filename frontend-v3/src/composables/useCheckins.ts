import { useQuery } from '@tanstack/vue-query'
import { toValue, type Ref } from 'vue'
import { checkinApi } from '@/api/checkin'

/**
 * 获取今日签到统计 - FE-003 修复后
 * 使用统一的 API 响应处理，无需手动检查 res.success
 */
export function useCheckinStats() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['checkin-stats'],
    queryFn: async () => {
      // FE-003: 直接获取数据，错误自动抛出
      return await checkinApi.getStats()
    },
    refetchInterval: 30000,
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}

/**
 * 获取今日签到列表 - FE-003 修复后
 * 使用统一的 API 响应处理，无需手动检查 res.success
 */
export function useTodayCheckins(className?: string | Ref<string>) {
  const { data, isPending, error, refetch } = useQuery({
    // FIX: 当 className 为空时，使用更精确的查询键，确保 invalidateQueries 能正确匹配
    queryKey: ['today-checkins', toValue(className) || 'all'],
    queryFn: async () => {
      const resolvedClassName = toValue(className)
      // FE-003: 直接获取数据，错误自动抛出
      return await checkinApi.getToday(resolvedClassName)
    },
    refetchInterval: 30000,
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}
