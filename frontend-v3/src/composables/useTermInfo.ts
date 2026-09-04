/**
 * 当前学期信息（周次计算基准）
 * 数据来源：后端 GET /api/term/current
 */
import { useQuery } from '@tanstack/vue-query'
import { termApi } from '@/api'

export function useTermInfo() {
  const { data, isPending, error } = useQuery({
    queryKey: ['term', 'current'],
    queryFn: () => termApi.getCurrent(),
    staleTime: 60 * 60 * 1000, // 学期信息几乎不变，1 小时缓存
    retry: 1,
  })
  return { data, isPending, error }
}
