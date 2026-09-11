import { get, post, put } from '@/lib/api'
import type { CourseOffering, EnrollmentRow } from '@/types'

/** 创建教学班请求 - 对应后端 CreateOfferingRequest */
export interface CreateOfferingRequest {
  course_id: number
  semester_id: number
  teacher_id?: number | null
  class_ids: number[]
  capacity?: number | null
}

/** 更新教学班请求 - 对应后端 UpdateOfferingRequest */
export interface UpdateOfferingRequest {
  teacher_id?: number | null
  class_ids?: number[]
  capacity?: number | null
  status?: 'active' | 'ended'
}

/** 导入选课请求 - 对应后端 ImportEnrollmentsRequest */
export interface ImportEnrollmentsRequest {
  student_ids: string[]
}

/** 我的教学班条目 - 对应后端 /teacher/offerings 响应 */
export interface TeacherOffering {
  id: number
  course_id: number
  course_name: string
  course_code: string
  teacher_name: string
  class_scope: string
  class_ids: number[]
  capacity: number | null
  status: 'active' | 'ended'
  enrolled_count: number
}

/**
 * 教学班管理 API（管理员）
 *
 * 后端路由: backend/app/api/routes/course_offerings.py
 */
export const offeringsApi = {
  /** 教学班列表（可按学期过滤，缺省当前学期） */
  list: (semesterId?: number): Promise<CourseOffering[]> =>
    get('/offerings', semesterId ? { semester_id: semesterId } : undefined),

  /** 我的教学班（教师：本学期本人授课；管理员：全部），含课程信息与选课人数 */
  listMine: (): Promise<TeacherOffering[]> =>
    get('/teacher/offerings'),

  create: (data: CreateOfferingRequest): Promise<CourseOffering> =>
    post('/offerings', data),

  update: (id: number, data: UpdateOfferingRequest): Promise<CourseOffering> =>
    put(`/offerings/${id}`, data),

  /** 教学班选课名单 */
  listEnrollments: (offeringId: number): Promise<EnrollmentRow[]> =>
    get(`/offerings/${offeringId}/enrollments`),

  /** 批量导入选课名单（逐个学号） */
  importEnrollments: (offeringId: number, studentIds: string[]): Promise<{ imported: number; skipped: number }> =>
    post(`/offerings/${offeringId}/enrollments`, { student_ids: studentIds }),

  /** 按班级加入名单（该班全部在读学生） */
  enrollByClass: (offeringId: number, classIds: number[]): Promise<{ imported: number; skipped: number }> =>
    post(`/offerings/${offeringId}/enrollments`, { class_ids: classIds }),

  /** 退课标记（保留历史） */
  dropEnrollment: (enrollmentId: number): Promise<void> =>
    put(`/enrollments/${enrollmentId}/drop`),
}
