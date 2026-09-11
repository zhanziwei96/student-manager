import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi } from '@/api'
import { toValue, type MaybeRefOrGetter } from 'vue'

export function useClassGroupSettings(classId: MaybeRefOrGetter<number | undefined>) {
  return useQuery({
    queryKey: ['class-group-settings', classId],
    queryFn: () => groupsApi.getClassGroupSettings(toValue(classId)!),
    enabled: () => !!toValue(classId),
  })
}

export function useUpdateClassGroupSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { class_id: number; max_members_per_group: number }) =>
      groupsApi.updateClassGroupSettings(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['class-group-settings', variables.class_id] })
    },
  })
}
