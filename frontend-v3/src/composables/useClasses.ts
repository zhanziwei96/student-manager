import { useQuery } from '@tanstack/vue-query'
import { classesApi } from '@/api/classes'
import { studentsApi } from '@/api/students'
import { computed, unref, type MaybeRefOrGetter } from 'vue'

/**
 * 班级数据 composable
 */
export function useClasses() {
  const { data: classNames, isPending, error, refetch } = useQuery({
    queryKey: ['classes'],
    queryFn: async () => {
      const res = await classesApi.getAll()
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch classes')
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
 * 获取班级统计信息（基于学生数据）
 */
export function useClassStats() {
  const { data: students, isPending, error } = useQuery({
    queryKey: ['students'],
    queryFn: async () => {
      const res = await studentsApi.getAll()
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch students')
    },
  })

  const classStats = computed(() => {
    if (!students.value) return []
    
    const stats = new Map<string, {
      name: string
      student_count: number
      total_score: number
      status: 'active' | 'inactive'
    }>()
    
    students.value.forEach(student => {
      const existing = stats.get(student.class_name)
      if (existing) {
        existing.student_count++
        existing.total_score += student.score
      } else {
        stats.set(student.class_name, {
          name: student.class_name,
          student_count: 1,
          total_score: student.score,
          status: 'active'
        })
      }
    })
    
    return Array.from(stats.values()).map(c => ({
      ...c,
      average_score: Math.round(c.total_score / c.student_count * 10) / 10
    })).sort((a, b) => a.name.localeCompare(b.name))
  })

  return {
    data: classStats,
    isPending,
    error,
  }
}

/**
 * 获取指定班级的学生列表
 */
export function useClassStudents(className: MaybeRefOrGetter<string>) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['class-students', className],
    queryFn: async () => {
      const name = unref(className)
      const res = await classesApi.getStudentsByClass(name)
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch class students')
    },
    enabled: () => !!unref(className),
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}
