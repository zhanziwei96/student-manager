import { get } from '@/lib/api'
import type { LeaderboardData } from '@/types'

export interface LeaderboardParams {
  scope?: 'class' | 'school'
  class_name?: string
  subject_id?: number // 科目ID（传则按科目分数排名）
  teacher_id?: number // 教师ID（可与 subject_id 组合：某教师的某科目排名）
  limit?: number
}

export const leaderboardApi = {
  getLeaderboard: async (params: LeaderboardParams = {}): Promise<LeaderboardData> => {
    const queryParams: Record<string, unknown> = {}
    if (params.scope) queryParams.scope = params.scope
    if (params.class_name) queryParams.class_name = params.class_name
    if (params.subject_id) queryParams.subject_id = params.subject_id
    if (params.teacher_id) queryParams.teacher_id = params.teacher_id
    if (params.limit) queryParams.limit = params.limit

    return get<LeaderboardData>('/students/leaderboard', queryParams)
  }
}
