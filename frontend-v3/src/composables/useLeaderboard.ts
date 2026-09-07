import { useQuery } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { leaderboardApi, type LeaderboardParams } from '@/api/leaderboard'

export function useLeaderboard(params?: LeaderboardParams | MaybeRefOrGetter<LeaderboardParams>) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['leaderboard', params],
    queryFn: async () => {
      // toValue 统一解包 ref/computed/getter/普通对象（含 subject_id/teacher_id 筛选参数）
      return await leaderboardApi.getLeaderboard(toValue(params) || {})
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
