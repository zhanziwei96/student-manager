/** 座位系统类型（与 backend/app/api/routes/classrooms.py 响应一致） */

export type SeatState = 'empty' | 'assigned' | 'occupied' | 'mine'

export interface SeatCell {
  seat_id: number
  seat_no: string
  row: number
  col: number
  is_broken: boolean
  state: SeatState
  student_id: string | null
  student_name: string | null
}

export interface ClassroomInfo {
  id: number
  name: string
  rows: number
  cols: number
  status: string
  seat_count: number
}

export interface SeatMapData {
  classroom: ClassroomInfo
  seats: SeatCell[]
}

export interface MySeatAssignment {
  classroom_id: number
  classroom_name: string
  seat_id: number
  seat_no: string
  is_broken: boolean
}
