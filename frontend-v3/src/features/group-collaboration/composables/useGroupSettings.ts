import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi } from '@/api'
import { toValue, type MaybeRefOrGetter } from 'vue'

export function useClassGroupSettings(className: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: ['class-group-settings', className],
    queryFn: () => groupsApi.getClassGroupSettings(toValue(className)),
    enabled: () => !!toValue(className),
  })
}

export function useUpdateClassGroupSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { class_name: string; max_members_per_group: number }) =>
      groupsApi.updateClassGroupSettings(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['class-group-settings', variables.class_name] })
    },
  })
}
