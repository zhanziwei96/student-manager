import { get, put } from '@/lib/api'

/** 个人成绩加减分请求 - 对应后端 UpdateEnrollmentScoreRequest */
export interface UpdateEnrollmentScoreRequest {
  score_change: number
  reason: string
}

/** 期末成绩登记请求 - 对应后端 SetFinalScoreRequest */
export interface SetFinalScoreRequest {
  final_score: number
}

/** 期末任务小组同分请求 - 对应后端 SetGroupFinalScoresRequest */
export interface SetGroupFinalScoresRequest {
  group_id: number
  final_score: number
}

/** 我的成绩条目 - 对应后端 GET /students/{id}/enrollments 响应 */
export interface MyEnrollment {
  enrollment_id: number
  course_id: number
  course_name: string
  teacher_name: string
  class_scope: string
  score: number
  final_score: number | null
  status: string
}

/** 成绩变更明细 - 对应后端 GET /enrollments/{id}/score-logs 响应 */
export interface EnrollmentScoreLog {
  id: number
  old_score: number | null
  new_score: number | null
  delta: number | null
  reason: string | null
  operator: string | null
  created_at: string
}

/**
 * 选课成绩 API - 个人成绩/期末成绩（授课教师）+ 我的成绩（学生）
 *
 * 后端路由: backend/app/api/routes/enrollments.py
 */
export const enrollmentsApi = {
  /** 我的成绩：当前学期选课列表 */
  getMyEnrollments: (studentId: string): Promise<MyEnrollment[]> =>
    get(`/students/${studentId}/enrollments`),

  /** 成绩变更明细（学生仅本人，教师/管理员不限） */
  getScoreLogs: (enrollmentId: number): Promise<EnrollmentScoreLog[]> =>
    get(`/enrollments/${enrollmentId}/score-logs`),

  /** 个人成绩加减分（乐观锁） */
  updateScore: (enrollmentId: number, data: UpdateEnrollmentScoreRequest): Promise<{ enrollment_id: number; score: number }> =>
    put(`/enrollments/${enrollmentId}/score`, data),

  /** 期末成绩登记（试卷个人分） */
  setFinalScore: (enrollmentId: number, data: SetFinalScoreRequest): Promise<{ enrollment_id: number; final_score: number }> =>
    put(`/enrollments/${enrollmentId}/final-score`, data),

  /** 期末成绩登记（任务小组同分） */
  setGroupFinalScores: (offeringId: number, data: SetGroupFinalScoresRequest): Promise<{ affected: number }> =>
    put(`/offerings/${offeringId}/final-scores/group`, data),
}
