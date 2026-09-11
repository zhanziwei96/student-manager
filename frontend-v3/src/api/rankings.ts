import { get } from '@/lib/api'

/** 排行榜查询参数 - 对应后端 /rankings */
export interface RankingParams {
  type: 'individual' | 'group'
  course_id: number
  scope: 'class' | 'all'
  class_id?: number
}

/** 个人榜条目 */
export interface RankingStudentEntry {
  rank: number
  student_id: string
  name: string
  class_name: string
  score: number
}

/** 小组榜条目 */
export interface RankingGroupEntry {
  rank: number
  group_id: number
  name: string
  class_name: string
  score: number
  members: string[]
}

export type RankingEntry = RankingStudentEntry | RankingGroupEntry

/** 排行榜响应数据 - 对应后端 /rankings 响应 */
export interface RankingData {
  type: 'individual' | 'group'
  scope: 'class' | 'all'
  course_name: string
  classes: string[]
  entries: RankingEntry[]
  my_rank: RankingStudentEntry | null
}

/**
 * 成绩排行榜 API - 教师 4 榜 / 学生本班榜
 *
 * 后端路由: backend/app/api/routes/rankings.py
 */
export const rankingsApi = {
  getRankings: (params: RankingParams): Promise<RankingData> =>
    get('/rankings', params as unknown as Record<string, unknown>),
}
