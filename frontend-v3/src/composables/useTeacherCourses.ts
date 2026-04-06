import { useQuery } from '@tanstack/vue-query'
import { schedulesApi } from '@/api/schedules'

/**
 * 获取当前教师的所有任教课程名称列表（去重）
 */
export function useTeacherCourses() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['teacher-courses'],
    queryFn: async () => {
      const schedules = await schedulesApi.getList()
      const courses = [...new Set(schedules.map(s => s.course_name).filter(Boolean))]
      return courses.sort()
    },
    staleTime: 5 * 60 * 1000, // 5 分钟内不重复请求
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}
