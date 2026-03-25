import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { usersApi, type CreateTeacherRequest, type UpdateTeacherRequest } from '@/api/users'

/**
 * Teachers query composable - FE-003 修复后
 * 使用统一的 API 响应处理，无需手动检查 res.success
 */
export function useTeachers() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['teachers'],
    queryFn: async () => {
      // FE-003: 直接获取数据，错误自动抛出
      return await usersApi.getTeachers()
    },
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}

export function useTeacherCreate() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (data: CreateTeacherRequest) => {
      // FE-003: 直接获取数据，错误自动抛出
      return await usersApi.create(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teachers'] })
    },
  })

  return {
    mutateAsync,
    isPending,
    error,
  }
}

export function useTeacherUpdate() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: UpdateTeacherRequest }) => {
      // FE-003: 直接获取数据，错误自动抛出
      return await usersApi.update(id, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teachers'] })
    },
  })

  return {
    mutateAsync,
    isPending,
    error,
  }
}

export function useTeacherDelete() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (id: number) => {
      // FE-003: 直接调用，错误自动抛出
      await usersApi.delete(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teachers'] })
    },
  })

  return {
    mutateAsync,
    isPending,
    error,
  }
}
