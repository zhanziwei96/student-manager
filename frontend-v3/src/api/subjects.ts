/**
 * 科目 API
 */
import { get, post, put } from '@/lib/api'

export interface Subject {
  id: number
  name: string
  semester: string
}

export const subjectsApi = {
  getAll: () => get<Subject[]>('/subjects'),
  update: (id: number, name: string) => put(`/subjects/${id}`, { name }),
  derive: () => post<{ created_count: number }>('/subjects/derive', {}),
}
