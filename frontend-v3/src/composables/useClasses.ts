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
 * 获取班级统计信息
 */
export function useClassStats() {
  const { data: classes, isPending, error } = useQuery({
    queryKey: ['classes'],
    queryFn: async () => {
      const res = await classesApi.getAll()
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch classes')
    },
  })

  const { data: students } = useQuery({
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
    if (!classes.value || !students.value) return []
    
    // 计算每个班级的学生数和平均分
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
    
    // 合并后端返回的班级状态
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
