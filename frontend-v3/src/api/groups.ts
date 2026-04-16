import { get, post, put, del } from '@/lib/api'

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

export interface TaskResultItem {
  group_id: number
  group_name: string
  teacher_scores: Record<string, number>
  peer_scores: Record<string, number>
  final_scores: Record<string, number>
  task_final: number
}

export interface TaskResultData {
  task: { id: number; title: string; status: string }
  dimensions: { id: number; name: string }[]
  results: Record<string, TaskResultItem>
}

export interface GroupTaskResult {
  task_id: number
  title: string
  status: string
  group_name: string
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

export interface DissolutionRequest {
  id: number
  group_id: number
  reason: string
  status: string
  created_at: string
}

export interface MyGroup {
  id: number
  name: string
  class_name: string
  leader_student_id: string
  is_leader: boolean
  members: { student_id: string; name: string }[]
  pending_requests: { id: number; student_id: string; created_at: string }[]
}

export const groupsApi = {
  // Teacher
  getTeacherTasks: (className: string): Promise<GroupTask[]> =>
    get('/teacher/group-tasks', { class_name: className }),
  createTask: (data: CreateGroupTaskRequest): Promise<{ task_id: number; status: string }> =>
    post('/teacher/group-tasks', data),
  startTask: (taskId: number): Promise<{ task_id: number; status: string }> =>
    post(`/teacher/group-tasks/${taskId}/start`, {}),
  closeTask: (taskId: number): Promise<{ task_id: number; status: string }> =>
    post(`/teacher/group-tasks/${taskId}/close`, {}),
  cloneTask: (taskId: number, targetClassName: string): Promise<{ task_id: number; status: string }> =>
    post(`/teacher/group-tasks/${taskId}/clone`, { target_class_name: targetClassName }),
  deleteTask: (taskId: number): Promise<unknown> =>
    del(`/teacher/group-tasks/${taskId}`),
  getTaskResults: (taskId: number): Promise<TaskResultData> =>
    get(`/teacher/group-tasks/${taskId}/results`),
  submitTeacherScore: (taskId: number, data: TeacherScoreRequest): Promise<unknown> =>
    post(`/teacher/group-tasks/${taskId}/scores`, data),
  getTeacherGroups: (className: string): Promise<Group[]> =>
    get('/teacher/groups', { class_name: className }),
  autoAssign: (className: string): Promise<Group[]> =>
    post('/teacher/groups/auto-assign', { class_name: className }),
  getClassGroupSettings: (className: string): Promise<{ class_name: string; max_members_per_group: number }> =>
    get('/teacher/class-group-settings', { class_name: className }),
  updateClassGroupSettings: (data: { class_name: string; max_members_per_group: number }): Promise<{ class_name: string; max_members_per_group: number }> =>
    put('/teacher/class-group-settings', data),
  transferLeader: (groupId: number, newLeaderId: string): Promise<{ leader_student_id: string }> =>
    post(`/teacher/groups/${groupId}/transfer-leader`, { new_leader_id: newLeaderId }),
  getDissolutionRequests: (): Promise<DissolutionRequest[]> =>
    get('/teacher/group-dissolution-requests'),
  approveDissolution: (reqId: number): Promise<unknown> =>
    post(`/teacher/group-dissolution-requests/${reqId}/approve`, {}),
  rejectDissolution: (reqId: number): Promise<unknown> =>
    post(`/teacher/group-dissolution-requests/${reqId}/reject`, {}),

  // Student
  createGroup: (className: string, name: string): Promise<unknown> =>
    post('/student/groups', { class_name: className, name }),
  getGroups: (className: string): Promise<Group[]> =>
    get('/student/groups', { class_name: className }),
  requestJoin: (groupId: number): Promise<unknown> =>
    post(`/student/groups/${groupId}/join-requests`, {}),
  approveJoin: (reqId: number): Promise<unknown> =>
    post(`/student/groups/join-requests/${reqId}/approve`, {}),
  rejectJoin: (reqId: number): Promise<unknown> =>
    post(`/student/groups/join-requests/${reqId}/reject`, {}),
  requestDissolution: (reason: string): Promise<unknown> =>
    post('/student/groups/dissolution-requests', { reason }),
  getStudentTasks: (): Promise<GroupTask[]> =>
    get('/student/group-tasks'),
  getEvaluations: (taskId: number): Promise<EvaluationTarget[]> =>
    get(`/student/group-tasks/${taskId}/evaluations`),
  submitStudentScores: (taskId: number, data: StudentScoresSubmit): Promise<unknown> =>
    post(`/student/group-tasks/${taskId}/scores`, data),
  getMyGroupResults: (): Promise<GroupTaskResult[]> =>
    get('/student/groups/my-group/results'),
  getMyGroup: (): Promise<MyGroup> =>
    get('/student/groups/my-group'),
}
