import { get, post, put } from '@/lib/api'

export interface CreateGroupTaskRequest {
  class_name: string
  title: string
  description?: string
  dimensions: string[]
}

export interface TeacherScoreRequest {
  target_group_id: number
  dimension_id: number
  score: number
}

export interface StudentScoreItem {
  dimension_id: number
  score: number
}

export interface StudentScoresSubmit {
  target_group_id: number
  scores: StudentScoreItem[]
}

export interface Group {
  id: number
  name: string
  leader_student_id: string
  member_count?: number
  max_members?: number | null
  is_full?: boolean
  leader_name?: string
  members?: { student_id: string; student_name?: string }[]
}

export interface GroupTask {
  id: number
  title: string
  status: 'preparing' | 'evaluating' | 'closed'
  class_name: string
}

export interface GroupTaskResult {
  task_id: number
  title: string
  status: string
  teacher_scores: Record<string, number>
  peer_scores: Record<string, number>
  final_scores: Record<string, number>
  task_final: number
}

export interface EvaluationTarget {
  target_group_id: number
  target_group_name: string
  dimensions: { id: number; name: string; scored: boolean }[]
  all_scored: boolean
}

export const groupsApi = {
  // Teacher
  getTeacherTasks: (className: string): Promise<GroupTask[]> =>
    get('/teacher/group-tasks', { class_name: className }),
  createTask: (data: CreateGroupTaskRequest): Promise<{ task_id: number; status: string }> =>
    post('/teacher/group-tasks', data),
  startTask: (taskId: number): Promise<any> =>
    post(`/teacher/group-tasks/${taskId}/start`, {}),
  closeTask: (taskId: number): Promise<any> =>
    post(`/teacher/group-tasks/${taskId}/close`, {}),
  getTaskResults: (taskId: number): Promise<any> =>
    get(`/teacher/group-tasks/${taskId}/results`),
  submitTeacherScore: (taskId: number, data: TeacherScoreRequest): Promise<any> =>
    post(`/teacher/group-tasks/${taskId}/scores`, data),
  getTeacherGroups: (className: string): Promise<Group[]> =>
    get('/teacher/groups', { class_name: className }),
  autoAssign: (className: string): Promise<any> =>
    post('/teacher/groups/auto-assign', { class_name: className }),
  getClassGroupSettings: (className: string): Promise<{ class_name: string; max_members_per_group: number }> =>
    get('/teacher/class-group-settings', { class_name: className }),
  updateClassGroupSettings: (data: { class_name: string; max_members_per_group: number }): Promise<{ class_name: string; max_members_per_group: number }> =>
    put('/teacher/class-group-settings', data),
  transferLeader: (groupId: number, newLeaderId: string): Promise<any> =>
    post(`/teacher/groups/${groupId}/transfer-leader`, { new_leader_id: newLeaderId }),
  getDissolutionRequests: (): Promise<any[]> =>
    get('/teacher/group-dissolution-requests'),
  approveDissolution: (reqId: number): Promise<any> =>
    post(`/teacher/group-dissolution-requests/${reqId}/approve`, {}),
  rejectDissolution: (reqId: number): Promise<any> =>
    post(`/teacher/group-dissolution-requests/${reqId}/reject`, {}),

  // Student
  createGroup: (className: string, name: string): Promise<any> =>
    post('/student/groups', { class_name: className, name }),
  getGroups: (className: string): Promise<Group[]> =>
    get('/student/groups', { class_name: className }),
  requestJoin: (groupId: number): Promise<any> =>
    post(`/student/groups/${groupId}/join-requests`, {}),
  approveJoin: (reqId: number): Promise<any> =>
    post(`/student/groups/join-requests/${reqId}/approve`, {}),
  rejectJoin: (reqId: number): Promise<any> =>
    post(`/student/groups/join-requests/${reqId}/reject`, {}),
  requestDissolution: (reason: string): Promise<any> =>
    post('/student/groups/dissolution-requests', { reason }),
  getStudentTasks: (): Promise<GroupTask[]> =>
    get('/student/group-tasks'),
  getEvaluations: (taskId: number): Promise<EvaluationTarget[]> =>
    get(`/student/group-tasks/${taskId}/evaluations`),
  submitStudentScores: (taskId: number, data: StudentScoresSubmit): Promise<any> =>
    post(`/student/group-tasks/${taskId}/scores`, data),
  getMyGroupResults: (): Promise<GroupTaskResult[]> =>
    get('/student/groups/my-group/results'),
  getMyGroup: (): Promise<any> =>
    get('/student/groups/my-group'),
}
