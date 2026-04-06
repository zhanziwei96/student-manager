import { get, post } from '@/lib/api'
import type { CourseSession, StartCourseSessionRequest } from '@/types'

export interface ActiveClassSession {
  course_name?: string
  class_name: string
  teacher_id: number
  teacher_name: string
  start_time: string
}

export const courseSessionApi = {
  getCurrent: (): Promise<CourseSession[]> =>
    get('/course-sessions'),

  start: (data: StartCourseSessionRequest): Promise<CourseSession> =>
    post('/course-sessions/start', data),

  end: (sessionId: number): Promise<void> =>
    post(`/course-sessions/${sessionId}/end`, {}),

  getActiveSessions: (): Promise<ActiveClassSession[]> =>
    get('/class-sessions/active'),

  getForClass: (className: string): Promise<{ active: boolean; id?: number; session_code?: string; course_name?: string; class_name?: string; teacher_name?: string; start_time?: string }> =>
    get(`/class-sessions/class/${encodeURIComponent(className)}`),

  getHistory: (): Promise<CourseSession[]> =>
    get('/course-sessions?status=ended'),
}
