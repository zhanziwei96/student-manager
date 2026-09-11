import { get, post, put, del } from '@/lib/api'
import type {
  Question,
  Answer,
  CreateQuestionRequest,
  CreateAnswerRequest,
  CreateReplyRequest,
  UpdateAnswerRequest,
} from '@/types/question'

// ============== 教师端 API ==============

/** 老师发布问题 */
export function createQuestion(data: CreateQuestionRequest): Promise<{ question_id: number }> {
  return post('/teacher/questions', data)
}

/** 老师获取问题列表 */
export function getTeacherQuestions(params?: { class_id?: number; status?: string }): Promise<Question[]> {
  return get('/teacher/questions', params)
}

/** 老师结束问题 */
export function closeQuestion(questionId: number): Promise<void> {
  return put(`/teacher/questions/${questionId}/close`)
}

/** 老师追问 */
export function replyAnswer(answerId: number, data: CreateReplyRequest): Promise<{ answer_id: number }> {
  return post(`/teacher/answers/${answerId}/reply`, data)
}

/** 老师标记优秀 */
export function starAnswer(answerId: number, starred: boolean = true): Promise<void> {
  return put(`/teacher/answers/${answerId}/star`, undefined, { starred: String(starred) })
}

// ============== 学生端 API ==============

/** 学生获取本班问题列表 */
export function getStudentQuestions(): Promise<Question[]> {
  return get('/student/questions')
}

/** 获取某问题的所有回答 */
export function getAnswers(questionId: number): Promise<Answer[]> {
  return get(`/student/questions/${questionId}/answers`)
}

/** 学生提交回答 */
export function createAnswer(data: CreateAnswerRequest): Promise<{ answer_id: number }> {
  return post('/student/answers', data)
}

/** 学生修改回答 */
export function updateAnswer(answerId: number, data: UpdateAnswerRequest): Promise<{ answer_id: number }> {
  return put(`/student/answers/${answerId}`, data)
}

/** 学生删除回答 */
export function deleteAnswer(answerId: number): Promise<void> {
  return del(`/student/answers/${answerId}`)
}
