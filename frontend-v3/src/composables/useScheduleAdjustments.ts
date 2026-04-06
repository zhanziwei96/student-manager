import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { scheduleAdjustmentApi } from '@/api'
import type { CreateScheduleAdjustmentRequest } from '@/types'

export function useCreateScheduleAdjustment() {
  const queryClient = useQueryClient()
  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (data: CreateScheduleAdjustmentRequest) => {
      await scheduleAdjustmentApi.create(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      queryClient.invalidateQueries({ queryKey: ['schedules', 'today'] })
    },
  })
  return { mutateAsync, isPending, error }
}
