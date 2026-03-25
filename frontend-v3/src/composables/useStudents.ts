import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { studentsApi } from '@/api'
import type { UpdateScoreRequest, CreateStudentRequest } from '@/types'

/**
 * Students query composable - FE-003 修复后
 * 使用统一的 API 响应处理，无需手动检查 res.success
 */
export function useStudents() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['students'],
    queryFn: async () => {
      // FE-003: 直接获取数据，错误自动抛出
      return await studentsApi.getAll()
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
      // FE-003: 直接获取数据，错误自动抛出
      return await studentsApi.updateScore(id, data)
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

export function useStudentCreate() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (data: CreateStudentRequest) => {
      // FE-003: 直接获取数据，错误自动抛出
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
