import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { studentsApi } from '@/api'
import type { UpdateScoreRequest } from '@/types'

/**
 * Students query composable
 * Based on: https://github.com/tanstack/query
 */
export function useStudents() {
  return useQuery({
    queryKey: ['students'],
    queryFn: async () => {
      const res = await studentsApi.getAll()
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch students')
    },
  })
}

export function useUpdateScore() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: UpdateScoreRequest }) => {
      const res = await studentsApi.updateScore(id, data)
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to update score')
    },
    onSuccess: () => {
      // Invalidate students cache
      queryClient.invalidateQueries({ queryKey: ['students'] })
      // Also invalidate stats
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}
