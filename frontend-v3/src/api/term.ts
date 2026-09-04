/**
 * 学期信息 API
 */
import { get } from '@/lib/api'

export interface TermInfo {
  term: string
  start_date: string
  current_week: number
  total_weeks: number
}

export const termApi = {
  getCurrent: () => get<TermInfo>('/term/current'),
}
