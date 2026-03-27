import { useQuery } from '@tanstack/vue-query'
import { classesApi } from '@/api/classes'
import { studentsApi } from '@/api/students'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

/**
 * 班级数据 composable - FE-003 修复后
 * 使用统一的 API 响应处理，无需手动检查 res.success
 */
export function useClasses() {
  const { data: classNames, isPending, error, refetch } = useQuery({
    queryKey: ['classes'],
    queryFn: async () => {
      // FE-003: 直接获取数据，错误自动抛出
      return await classesApi.getAll()
    },
  })

  return {
    data: classNames,
    isPending,
    error,
    refetch,
  }
}

/**
 * 获取班级统计信息 - FE-003 修复后
 */
export function useClassStats() {
  const { data: classes, isPending, error } = useQuery({
    queryKey: ['classes'],
    queryFn: async () => {
      // FE-003: 直接获取数据，错误自动抛出
      return await classesApi.getAll()
    },
  })

  const { data: students } = useQuery({
    queryKey: ['students'],
    queryFn: async () => {
      // FE-003: 直接获取数据，错误自动抛出
      return await studentsApi.getAll()
    },
  })

  const classStats = computed(() => {
    if (!classes.value || !students.value) return []

    const classMap = new Map<string, {
      student_count: number
      total_score: number
    }>()

    students.value.forEach(student => {
      const existing = classMap.get(student.class_name)
      if (existing) {
        existing.student_count++
        existing.total_score += student.score
      } else {
        classMap.set(student.class_name, {
          student_count: 1,
          total_score: student.score,
        })
      }
    })

    return classes.value.map(cls => {
      const stats = classMap.get(cls.name) || { student_count: 0, total_score: 0 }
      return {
        name: cls.name,
        status: cls.status,
        student_count: stats.student_count,
        average_score: stats.student_count > 0
          ? Math.round(stats.total_score / stats.student_count * 10) / 10
          : 0
      }
    }).sort((a, b) => a.name.localeCompare(b.name))
  })

  return {
    data: classStats,
    isPending,
    error,
  }
}

/**
 * 获取指定班级的学生列表 - FE-003 修复后
 */
export function useClassStudents(className: MaybeRefOrGetter<string>) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['class-students', className],
    queryFn: async () => {
      const name = toValue(className)
      // FE-003: 直接获取数据，错误自动抛出
      return await classesApi.getStudentsByClass(name)
    },
    enabled: () => !!toValue(className),
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}
