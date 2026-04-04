import { get } from '@/lib/api'
import type { LeaderboardData } from '@/types'

export interface LeaderboardParams {
  scope?: 'class' | 'school'
  class_name?: string
  limit?: number
}

export const leaderboardApi = {
  getLeaderboard: async (params: LeaderboardParams = {}): Promise<LeaderboardData> => {
    const queryParams: Record<string, unknown> = {}
    if (params.scope) queryParams.scope = params.scope
    if (params.class_name) queryParams.class_name = params.class_name
    if (params.limit) queryParams.limit = params.limit

    return get<LeaderboardData>('/students/leaderboard', queryParams)
  }
}
