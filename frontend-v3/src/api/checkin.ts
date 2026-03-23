import { api } from '@/lib/api'
import type {
  ApiResponse,
  CheckinRequest,
  CheckinRecord,
} from '@/types'

export const checkinApi = {
  checkin: (data: CheckinRequest): Promise<ApiResponse<CheckinRecord>> =>
    api('/checkin', { method: 'POST', body: data }),

  getTodayRecords: (): Promise<ApiResponse<CheckinRecord[]>> =>
    api('/checkins/today', { method: 'GET' }),

  getStats: (): Promise<ApiResponse<{
    total: number
    checked_in: number
    rate: number
  }>> =>
    api('/checkins/stats', { method: 'GET' }),

  teacherCheckin: (studentId: string): Promise<ApiResponse<CheckinRecord>> =>
    api('/teacher-checkin', {
      method: 'POST',
      body: { student_id: studentId },
    }),
}
