import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi } from '@/api'

export function useStudentGroupTasks() {
  return useQuery({
    queryKey: ['student-group-tasks'],
    queryFn: () => groupsApi.getStudentTasks(),
  })
}

export function useEvaluations(taskId: number) {
  return useQuery({
    queryKey: ['evaluations', taskId],
    queryFn: () => groupsApi.getEvaluations(taskId),
    enabled: !!taskId,
  })
}

export function useSubmitStudentScores() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: number; data: any }) =>
      groupsApi.submitStudentScores(taskId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluations'] })
    },
  })
}

export function useMyGroupResults() {
  return useQuery({
    queryKey: ['my-group-results'],
    queryFn: () => groupsApi.getMyGroupResults(),
  })
}
