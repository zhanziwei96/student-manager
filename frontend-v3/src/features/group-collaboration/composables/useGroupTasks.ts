import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi } from '@/api'

export function useCreateGroupTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: groupsApi.createTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['group-tasks'] })
    },
  })
}

export function useStartGroupTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId }: { taskId: number }) => groupsApi.startTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['group-tasks'] })
    },
  })
}

export function useCloseGroupTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId }: { taskId: number }) => groupsApi.closeTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['group-tasks'] })
    },
  })
}

export function useTaskResults(taskId: number) {
  return useQuery({
    queryKey: ['group-task-results', taskId],
    queryFn: () => groupsApi.getTaskResults(taskId),
    enabled: !!taskId,
  })
}

export function useSubmitTeacherScore() {
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: number; data: any }) =>
      groupsApi.submitTeacherScore(taskId, data),
  })
}
