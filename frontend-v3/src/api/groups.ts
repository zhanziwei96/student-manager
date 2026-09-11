import { get, post, put, del } from '@/lib/api'
import type { GroupDetail } from '@/types'

/** 小组 - 对应后端 GET /teacher/groups 响应（小组按课程划分） */
export interface Group {
  id: number
  name: string
  leader_student_id: string
  leader_name?: string
  course_id: number | null
  course_name?: string | null
  score?: number
  members?: { student_id: string; name?: string }[]
  // 学生可加入小组列表字段（GET /student/groups）
  member_count?: number
  max_members?: number | null
  is_full?: boolean
}

/** 我的小组条目 - 对应后端 GET /student/groups/my-group 响应 */
export interface MyGroup {
  id: number
  name: string
  class_name: string
  course_id: number | null
  course_name?: string | null
  score: number
  leader_student_id: string
  leader_name?: string
  is_leader: boolean
  members: { student_id: string; name: string }[]
  pending_requests: { id: number; student_id: string; created_at: string }[]
}

export interface GroupScoreLog {
  old_score: number | null
  new_score: number | null
  delta: number | null
  reason: string | null
  operator: string | null
  created_at: string
}

export interface DissolutionRequest {
  id: number
  group_id: number
  reason: string
  status: string
  created_at: string
  group_name?: string
}

/**
 * 小组 API - 科目式小组（课程维度，持续一学期，累计分）
 *
 * 后端路由: backend/app/api/routes/groups.py + group_scores.py
 */
export const groupsApi = {
  // 教师
  getTeacherGroups: (classId: number, courseId?: number): Promise<Group[]> =>
    get('/teacher/groups', courseId ? { class_id: classId, course_id: courseId } : { class_id: classId }),
  createTeacherGroup: (data: { class_id: number; name: string; course_id: number }): Promise<{ group_id: number; name: string }> =>
    post('/teacher/groups', data),
  autoAssign: (classId: number, courseId: number): Promise<Group[]> =>
    post('/teacher/groups/auto-assign', { class_id: classId, course_id: courseId }),
  getClassGroupSettings: (classId: number): Promise<{ class_name: string; max_members_per_group: number }> =>
    get('/teacher/class-group-settings', { class_id: classId }),
  updateClassGroupSettings: (data: { class_id: number; max_members_per_group: number }): Promise<{ class_name: string; max_members_per_group: number }> =>
    put('/teacher/class-group-settings', data),
  transferLeader: (groupId: number, newLeaderId: string): Promise<{ leader_student_id: string }> =>
    post(`/teacher/groups/${groupId}/transfer-leader`, { new_leader_id: newLeaderId }),
  getGroupDetail: (groupId: number): Promise<GroupDetail> =>
    get(`/teacher/groups/${groupId}`),
  removeMember: (groupId: number, studentId: string): Promise<unknown> =>
    del(`/teacher/groups/${groupId}/members/${studentId}`),
  dissolveGroup: (groupId: number): Promise<unknown> =>
    del(`/teacher/groups/${groupId}`),
  updateScore: (groupId: number, scoreChange: number, reason: string): Promise<unknown> =>
    put(`/groups/${groupId}/score`, { score_change: scoreChange, reason }),
  getScoreLogs: (groupId: number, params?: { limit?: number; offset?: number }): Promise<GroupScoreLog[]> =>
    get(`/groups/${groupId}/score-logs`, params),
  getDissolutionRequests: (): Promise<DissolutionRequest[]> =>
    get('/teacher/group-dissolution-requests'),
  approveDissolution: (reqId: number): Promise<unknown> =>
    post(`/teacher/group-dissolution-requests/${reqId}/approve`, {}),
  rejectDissolution: (reqId: number): Promise<unknown> =>
    post(`/teacher/group-dissolution-requests/${reqId}/reject`, {}),

  // 学生
  createGroup: (className: string, name: string, courseId: number): Promise<{ group_id: number; name: string }> =>
    post('/student/groups', { class_name: className, name, course_id: courseId }),
  getGroups: (className: string, courseId?: number): Promise<Group[]> =>
    get('/student/groups', courseId ? { class_name: className, course_id: courseId } : { class_name: className }),
  requestJoin: (groupId: number): Promise<unknown> =>
    post(`/student/groups/${groupId}/join-requests`, {}),
  approveJoin: (reqId: number): Promise<unknown> =>
    post(`/student/groups/join-requests/${reqId}/approve`, {}),
  rejectJoin: (reqId: number): Promise<unknown> =>
    post(`/student/groups/join-requests/${reqId}/reject`, {}),
  requestDissolution: (reason: string): Promise<unknown> =>
    post('/student/groups/dissolution-requests', { reason }),
  leaveGroup: (): Promise<unknown> =>
    post('/student/groups/leave', {}),
  getMyGroups: (): Promise<MyGroup[]> =>
    get('/student/groups/my-group'),
}
