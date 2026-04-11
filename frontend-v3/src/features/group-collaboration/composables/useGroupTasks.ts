import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi } from '@/api'

import { toValue, type MaybeRefOrGetter } from 'vue'

export function useTeacherGroupTasks(className: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: ['group-tasks', className],
    queryFn: () => groupsApi.getTeacherTasks(toValue(className)),
    enabled: () => !!toValue(className),
  })
}

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
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: number; data: any }) =>
      groupsApi.submitTeacherScore(taskId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['group-task-results', variables.taskId] })
    },
  })
}
