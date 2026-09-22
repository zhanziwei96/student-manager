// get 的签名是 get<T>(url, params?, options?) —— params 是第二个位置参数，不是 { params }
import { get, post, put, del } from '@/lib/api'
import type { ClassroomInfo, MySeatAssignment, SeatMapData } from '@/types/seats'

export const classroomsApi = {
  list: () => get<ClassroomInfo[]>('/classrooms'),
  create: (data: { name: string; rows: number; cols: number }) =>
    post<ClassroomInfo>('/classrooms', data),
  update: (id: number, data: { name?: string; rows?: number; cols?: number; status?: string }) =>
    put<ClassroomInfo>(`/classrooms/${id}`, data),
  getSeats: (id: number, sessionId?: number | null) =>
    get<SeatMapData>(
      `/classrooms/${id}/seats`,
      sessionId != null ? { session_id: sessionId } : undefined,
    ),
}

export const seatsApi = {
  setBroken: (seatId: number, isBroken: boolean) =>
    post<{ id: number; is_broken: boolean }>(`/seats/${seatId}/broken`, { is_broken: isBroken }),
}

export const seatAssignmentsApi = {
  mine: () => get<MySeatAssignment[]>('/seat-assignments/mine'),
}

export const seatOverridesApi = {
  set: (sessionId: number, studentId: string, seatId: number) =>
    post(`/sessions/${sessionId}/seat-overrides`, { student_id: studentId, seat_id: seatId }),
  clear: (sessionId: number, studentId: string) =>
    del(`/sessions/${sessionId}/seat-overrides/${studentId}`),
}
