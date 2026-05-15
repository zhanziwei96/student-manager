/**
 * 失物招领类型定义
 */

export type LostFoundStatus = 'open' | 'claiming' | 'closed'
export type ClaimStatus = 'pending' | 'confirmed' | 'rejected'

export interface TeacherLostFoundItem {
  id: number
  title: string
  description: string
  location?: string
  image_url?: string
  status: LostFoundStatus
  publisher_id: number
  created_at: string
  updated_at: string
  pending_count: number
  total_claims: number
}

export interface TeacherLostFoundDetail {
  id: number
  title: string
  description: string
  location?: string
  image_url?: string
  status: LostFoundStatus
  publisher_id: number
  publisher_name?: string
  created_at: string
  updated_at: string
  comments: LostFoundComment[]
  claims: LostFoundClaim[]
  pending_count: number
}

export interface StudentLostFoundItem {
  id: number
  title: string
  description: string
  location?: string
  image_url?: string
  status: LostFoundStatus
  publisher_name?: string
  created_at: string
  updated_at: string
}

export interface StudentLostFoundDetail {
  id: number
  title: string
  description: string
  location?: string
  image_url?: string
  status: LostFoundStatus
  publisher_name?: string
  created_at: string
  updated_at: string
  comments: LostFoundCommentAnonymous[]
  my_claim?: MyClaimInfo
}

export interface LostFoundComment {
  id: number
  item_id: number
  user_id: number
  user_name?: string
  content: string
  created_at: string
}

export interface LostFoundCommentAnonymous {
  id: number
  content: string
  user_name: string
  created_at: string
}

export interface LostFoundClaim {
  id: number
  item_id: number
  student_id: number
  student_name?: string
  contact: string
  message?: string
  status: ClaimStatus
  created_at: string
}

export interface MyClaimInfo {
  id: number
  status: ClaimStatus
  created_at: string
}

export interface CreateLostFoundCommentRequest {
  content: string
}

export interface CreateLostFoundClaimRequest {
  contact: string
  message?: string
}

export interface LostFoundQueryParams {
  keyword?: string
  status?: LostFoundStatus
  page?: number
  page_size?: number
}

export interface LostFoundListResponse<T> {
  items: T[]
  total: number
}
