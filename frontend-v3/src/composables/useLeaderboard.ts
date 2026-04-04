import { useQuery } from '@tanstack/vue-query'
import { computed, type Ref } from 'vue'
import { leaderboardApi, type LeaderboardParams } from '@/api/leaderboard'

export function useLeaderboard(params?: LeaderboardParams | Ref<LeaderboardParams>) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['leaderboard', params],
    queryFn: async () => {
      const resolvedParams = params && 'value' in params ? params.value : params
      return await leaderboardApi.getLeaderboard(resolvedParams || {})
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  })

  return {
    data,
    isPending,
    error,
    refetch,
    students: computed(() => data.value?.students || []),
    myRank: computed(() => data.value?.my_rank || null),
    total: computed(() => data.value?.total || 0),
  }
}
