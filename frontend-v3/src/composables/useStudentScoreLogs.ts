import { useQuery } from '@tanstack/vue-query'
import { studentsApi } from '@/api/students'
import { toValue, type MaybeRefOrGetter } from 'vue'

interface UseStudentScoreLogsOptions {
  limit?: number
}

/**
 * 获取学生分数历史记录
 * @param limit - 限制数量，默认 50；传入 0 表示不限制
 */
export function useStudentScoreLogs(
  studentId: MaybeRefOrGetter<string>,
  options?: UseStudentScoreLogsOptions,
) {
  return useQuery({
    queryKey: ['student-score-logs', studentId, options?.limit],
    queryFn: () => studentsApi.getScoreLogs(toValue(studentId), options?.limit),
    enabled: () => !!toValue(studentId),
  })
}
