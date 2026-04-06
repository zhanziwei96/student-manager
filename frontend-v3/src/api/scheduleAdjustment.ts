import { get, post } from '@/lib/api'
import type { ScheduleAdjustment, CreateScheduleAdjustmentRequest } from '@/types'

export const scheduleAdjustmentApi = {
  create: (data: CreateScheduleAdjustmentRequest): Promise<void> =>
    post('/schedule-adjustments', data),

  list: (params?: { schedule_id?: number; week_number?: number }): Promise<ScheduleAdjustment[]> => {
    const query = params
      ? '?' + new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])).toString()
      : ''
    return get(`/schedule-adjustments${query}`)
  },
}
