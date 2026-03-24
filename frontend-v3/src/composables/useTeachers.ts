import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { usersApi, type CreateTeacherRequest, type UpdateTeacherRequest } from '@/api/users'

/**
 * Teachers query composable
 */
export function useTeachers() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['teachers'],
    queryFn: async () => {
      const res = await usersApi.getTeachers()
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch teachers')
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
      const res = await usersApi.create(data)
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to create teacher')
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
      const res = await usersApi.update(id, data)
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to update teacher')
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
      const res = await usersApi.delete(id)
      if (res.success) {
        return res
      }
      throw new Error(res.message || 'Failed to delete teacher')
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
