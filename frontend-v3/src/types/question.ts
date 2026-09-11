/**
 * 课堂问答类型定义
 */

/** 问题状态 */
export type QuestionStatus = 'active' | 'closed'

/** 问题列表项 */
export interface Question {
  id: number
  teacher_id: number
  teacher_name?: string
  class_name?: string
  content: string
  status: QuestionStatus
  is_realtime: boolean
  answer_count: number
  created_at: string
  closed_at?: string
}

/** 回答 */
export interface Answer {
  id: number
  question_id: number
  student_id: string
  student_name?: string
  content: string
  is_anonymous: boolean
  is_starred: boolean
  parent_id?: number
  created_at: string
  is_own: boolean
}

/** 创建问题请求 */
export interface CreateQuestionRequest {
  content: string
  class_id?: number
  is_realtime?: boolean
}

/** 创建回答请求 */
export interface CreateAnswerRequest {
  question_id: number
  content: string
  is_anonymous?: boolean
}

/** 创建追问请求 */
export interface CreateReplyRequest {
  answer_id: number
  content: string
}

/** 更新回答请求 */
export interface UpdateAnswerRequest {
  content: string
}
