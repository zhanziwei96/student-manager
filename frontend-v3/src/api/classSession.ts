import { api } from '@/lib/api'
import type {
  ApiResponse,
  ClassSession,
  StartClassRequest,
} from '@/types'

export const classSessionApi = {
  getCurrent: (): Promise<ApiResponse<ClassSession | null>> =>
    api('/class-session', { method: 'GET' }),

  start: (data: StartClassRequest): Promise<ApiResponse<ClassSession>> =>
    api('/class-session/start', { method: 'POST', body: data }),

  end: (): Promise<ApiResponse<ClassSession>> =>
    api('/class-session/end', { method: 'POST' }),

  getStudents: (): Promise<ApiResponse<{
    students: Array<{
      id: number
      student_id: string
      name: string
      checked_in: boolean
      checkin_time?: string
    }>
  }>> =>
    api('/class-session/students', { method: 'GET' }),
}
