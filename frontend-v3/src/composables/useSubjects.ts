/**
 * 科目列表
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { subjectsApi } from '@/api'

export function useSubjects() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['subjects'],
    queryFn: () => subjectsApi.getAll(),
    staleTime: 5 * 60 * 1000, // 5 分钟
  })
  return { data, isPending, error, refetch }
}

export function useUpdateSubject() {
  const queryClient = useQueryClient()
  const { mutateAsync, isPending } = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      subjectsApi.update(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subjects'] })
    },
  })
  return { mutateAsync, isPending }
}

export function useDeriveSubjects() {
  const queryClient = useQueryClient()
  const { mutateAsync, isPending } = useMutation({
    mutationFn: () => subjectsApi.derive(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subjects'] })
    },
  })
  return { mutateAsync, isPending }
}
