import { useQuery } from '@tanstack/vue-query'
import { classesApi } from '@/api/classes'
import { studentsApi } from '@/api/students'
import { toValue, type MaybeRefOrGetter } from 'vue'

/**
 * 班级数据 composable
 *
 * 班级列表来自 /classes 管理接口（含学生数），
 * 教师端/管理端共用；教师端 Phase 4b 改造后按教学班维度取数。
 */
export function useClasses() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['classes'],
    queryFn: () => classesApi.list(),
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}

/**
 * 获取指定班级的学生列表
 */
export function useClassStudents(className: MaybeRefOrGetter<string>) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['class-students', className],
    queryFn: () => studentsApi.getStudentsByClass(toValue(className)),
    enabled: () => !!toValue(className),
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}
