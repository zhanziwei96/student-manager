import { useQuery } from '@tanstack/vue-query'
import { statsApi } from '@/api'

/**
 * Stats query composable - FE-003 修复后
 * 使用统一的 API 响应处理，无需手动检查 res.success
 */
export function useStats() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      // FE-003: 直接获取数据，错误自动抛出
      return await statsApi.getStats()
    },
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}
