import { useQuery } from '@tanstack/vue-query'
import { statsApi } from '@/api'

/**
 * Stats query composable
 * Based on: https://github.com/tanstack/query
 */
export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const res = await statsApi.getAll()
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch stats')
    },
  })
}
