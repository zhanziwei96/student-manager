import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { studentsApi } from '@/api'
import type { CreateStudentRequest } from '@/types'

/**
 * Students query composable - FE-006 修复
 * 使用统一的 API 响应处理，无需手动检查 res.success
 */
export function useStudents() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['students'],
    queryFn: async () => {
      return await studentsApi.getAll()
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}

export function useStudentCreate() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (data: CreateStudentRequest) => {
      return await studentsApi.create(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  return {
    mutateAsync,
    isPending,
    error,
  }
}
