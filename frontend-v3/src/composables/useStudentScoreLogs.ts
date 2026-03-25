import { useQuery } from '@tanstack/vue-query'
import { studentsApi } from '@/api/students'
import { toValue, type MaybeRefOrGetter } from 'vue'

/**
 * 获取学生分数历史记录
 */
export function useStudentScoreLogs(studentId: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: ['student-score-logs', studentId],
    queryFn: () => studentsApi.getScoreLogs(toValue(studentId)),
    enabled: () => !!toValue(studentId),
  })
}
