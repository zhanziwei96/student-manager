import { useQuery } from '@tanstack/vue-query'
import { classesApi } from '@/api'

/**
 * Classes query composable
 * Fetches list of all class names
 */
export function useClasses() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['classes'],
    queryFn: async () => {
      const res = await classesApi.getAll()
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch classes')
    },
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}
