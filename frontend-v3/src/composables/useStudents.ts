import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { studentsApi } from '@/api'
import type { UpdateScoreRequest, CreateStudentRequest } from '@/types'

/**
 * Students query composable
 * Based on: https://github.com/tanstack/query
 */
export function useStudents() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['students'],
    queryFn: async () => {
      const res = await studentsApi.getAll()
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch students')
    },
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}

export function useScoreUpdate() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: UpdateScoreRequest }) => {
      const res = await studentsApi.updateScore(id, data)
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to update score')
    },
    onSuccess: () => {
      // 使学生缓存失效
      queryClient.invalidateQueries({ queryKey: ['students'] })
      // 同时使统计数据失效
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  return {
    mutateAsync,
    isPending,
    error,
  }
}

export function useStudentCreate() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (data: CreateStudentRequest) => {
      const res = await studentsApi.create(data)
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to create student')
    },
    onSuccess: () => {
      // 使学生缓存失效
      queryClient.invalidateQueries({ queryKey: ['students'] })
      // 同时使统计数据失效
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  return {
    mutateAsync,
    isPending,
    error,
  }
}
