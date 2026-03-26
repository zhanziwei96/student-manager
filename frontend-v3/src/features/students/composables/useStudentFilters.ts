import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import type { Student, GroupedStudents, ClassOption, StudentFilterState } from '../types'

/**
 * 学生筛选 Composable
 * 
 * 提供学生列表的筛选和分组功能
 */
export function useStudentFilters(students: Ref<Student[] | undefined>) {
  // 筛选条件
  const filters = ref<StudentFilterState>({
    searchQuery: '',
    className: '',
  })

  // 按班级分组的学生
  const studentsByClass = computed<GroupedStudents>(() => {
    if (!students.value) return {}

    const grouped: GroupedStudents = {}
    students.value.forEach((student) => {
      const className = student.class_name || '未分班'
      if (!grouped[className]) {
        grouped[className] = []
      }
      grouped[className].push(student)
    })
    return grouped
  })

  // 班级列表（包含学生数量）
  const classList = computed(() => {
    const list = Object.entries(studentsByClass.value).map(([name, students]) => ({
      name,
      count: students.length,
    }))
    return list.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
  })

  // 班级下拉选项
  const classOptions = computed<ClassOption[]>(() => [
    { value: '', label: '全部班级', count: students.value?.length || 0 },
    ...classList.value.map((c) => ({
      value: c.name,
      label: `${c.name} (${c.count}人)`,
      count: c.count,
    })),
  ])

  // 过滤后的学生列表
  const filteredStudents = computed<Student[]>(() => {
    if (!students.value) return []

    let result = [...students.value]

    // 按班级筛选
    if (filters.value.className) {
      result = result.filter((s) => s.class_name === filters.value.className)
    }

    // 按搜索词筛选
    if (filters.value.searchQuery) {
      const query = filters.value.searchQuery.toLowerCase()
      result = result.filter(
        (s) =>
          s.name.toLowerCase().includes(query) ||
          s.student_id.toLowerCase().includes(query) ||
          s.class_name.toLowerCase().includes(query)
      )
    }

    return result
  })

  // 设置筛选条件
  const setSearchQuery = (query: string) => {
    filters.value.searchQuery = query
  }

  const setClassFilter = (className: string) => {
    filters.value.className = className
  }

  // 默认选中第一个班级（如果当前未选择）
  const selectFirstClass = () => {
    if (classList.value.length > 0 && !filters.value.className) {
      filters.value.className = classList.value[0].name
    }
  }

  return {
    filters,
    studentsByClass,
    classList,
    classOptions,
    filteredStudents,
    setSearchQuery,
    setClassFilter,
    selectFirstClass,
  }
}
