import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi, type StudentScoresSubmit } from '@/api'
import { toValue, type MaybeRefOrGetter } from 'vue'

export function useStudentGroupTasks() {
  return useQuery({
    queryKey: ['student-group-tasks'],
    queryFn: () => groupsApi.getStudentTasks(),
  })
}

export function useEvaluations(taskId: MaybeRefOrGetter<number>) {
  return useQuery({
    queryKey: ['evaluations', taskId],
    queryFn: () => groupsApi.getEvaluations(toValue(taskId)),
    enabled: () => !!toValue(taskId),
  })
}

export function useSubmitStudentScores() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: number; data: StudentScoresSubmit }) =>
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
