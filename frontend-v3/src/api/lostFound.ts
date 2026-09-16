/**
 * 失物招领 API
 */
import { get, post, put, del } from '@/lib/api'
import type {
  TeacherLostFoundItem,
  TeacherLostFoundDetail,
  StudentLostFoundItem,
  StudentLostFoundDetail,
  LostFoundListResponse,
  CreateLostFoundCommentRequest,
  CreateLostFoundClaimRequest,
  LostFoundQueryParams,
} from '@/types/lostFound'

// ============== 教师端 API ==============

export async function createLostFoundItem(data: {
  title: string
  description: string
  location?: string
  file?: File
  class_ids?: number[]
}): Promise<{ item_id: number }> {
  const formData = new FormData()
  formData.append('title', data.title)
  formData.append('description', data.description)
  if (data.location) formData.append('location', data.location)
  if (data.file) formData.append('image', data.file)
  // 每个勾选班级一个 class_ids 重复字段；空选不传（后端默认 [] = 所有班级可见）
  for (const classId of data.class_ids ?? []) formData.append('class_ids', String(classId))
  return post('/teacher/lost-found', formData)
}

export function getTeacherLostFoundItems(params?: LostFoundQueryParams): Promise<LostFoundListResponse<TeacherLostFoundItem>> {
  return get('/teacher/lost-found', params as Record<string, unknown>)
}

export function getTeacherLostFoundDetail(id: number): Promise<TeacherLostFoundDetail> {
  return get(`/teacher/lost-found/${id}`)
}

export async function updateLostFoundItem(id: number, data: {
  title?: string
  description?: string
  location?: string
  file?: File
  class_ids?: number[]
}): Promise<void> {
  const formData = new FormData()
  if (data.title) formData.append('title', data.title)
  if (data.description) formData.append('description', data.description)
  if (data.location) formData.append('location', data.location)
  if (data.file) formData.append('image', data.file)
  // 每个勾选班级一个 class_ids 重复字段；空选不传（后端 None = 保持原范围不变）
  for (const classId of data.class_ids ?? []) formData.append('class_ids', String(classId))
  return put(`/teacher/lost-found/${id}`, formData)
}

export function deleteLostFoundItem(id: number): Promise<void> {
  return del(`/teacher/lost-found/${id}`)
}

export function confirmClaim(itemId: number, claimId: number): Promise<void> {
  return put(`/teacher/lost-found/${itemId}/claims/${claimId}/confirm`)
}

export function rejectClaim(itemId: number, claimId: number): Promise<void> {
  return put(`/teacher/lost-found/${itemId}/claims/${claimId}/reject`)
}

// ============== 学生端 API ==============

export function getStudentLostFoundItems(params?: LostFoundQueryParams): Promise<LostFoundListResponse<StudentLostFoundItem>> {
  return get('/student/lost-found', params as Record<string, unknown>)
}

export function getStudentLostFoundDetail(id: number): Promise<StudentLostFoundDetail> {
  return get(`/student/lost-found/${id}`)
}

export function createLostFoundComment(itemId: number, data: CreateLostFoundCommentRequest): Promise<{ id: number }> {
  return post(`/student/lost-found/${itemId}/comments`, data)
}

export function claimLostFoundItem(itemId: number, data: CreateLostFoundClaimRequest): Promise<{ id: number }> {
  return post(`/student/lost-found/${itemId}/claim`, data)
}
