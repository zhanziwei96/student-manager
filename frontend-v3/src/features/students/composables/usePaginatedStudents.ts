import { ref, computed, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { studentsApi } from '@/api'
import { classesApi } from '@/api/classes'
import type { Student } from '@/types'
import type { ClassOption } from '../types'

/**
 * 学生列表分页 Composable（admin/teacher 学生管理页共用）
 *
 * - 浏览模式：服务端分页（limit/offset），total 由后端返回
 * - 搜索模式：拉取当前班级筛选下的全量数据，前端按关键词过滤
 *   （搜索需跨页匹配，故搜索时不分页）
 * - 班级选项来自 /classes 接口，不再依赖全量学生列表
 */
export function usePaginatedStudents(pageSize = 50) {
  const page = ref(1)
  const searchQuery = ref('')
  const className = ref('')

  const isSearching = computed(() => searchQuery.value.trim().length > 0)

  // 班级选项（/classes 接口：班级管理列表，含学生数）
  const { data: classes } = useQuery({
    queryKey: ['classes'],
    queryFn: () => classesApi.list(),
    staleTime: 1000 * 60 * 5,
  })

  const classOptions = computed<ClassOption[]>(() => [
    { value: '', label: '全部班级', count: 0 },
    ...(classes.value ?? []).map((c) => ({ value: c.name, label: c.name, count: 0 })),
  ])

  // 查询参数：搜索时不分页（拉全量前端过滤），否则服务端分页
  const queryParams = computed(() => ({
    class_name: className.value || undefined,
    limit: isSearching.value ? undefined : pageSize,
    offset: isSearching.value ? undefined : (page.value - 1) * pageSize,
  }))

  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['students', 'paginated', queryParams],
    queryFn: () => studentsApi.getPaginated(queryParams.value),
    staleTime: 1000 * 60 * 5,
  })

  const items = computed(() => data.value?.items ?? [])
  const total = computed(() => data.value?.total ?? items.value.length)
  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

  // 展示列表：搜索模式前端过滤，分页模式直接展示当前页
  const filteredStudents = computed<Student[]>(() => {
    if (!isSearching.value) return items.value
    const q = searchQuery.value.trim().toLowerCase()
    return items.value.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.student_id.toLowerCase().includes(q) ||
        s.class_name.toLowerCase().includes(q),
    )
  })

  // 切换班级/搜索时回到第一页
  watch([searchQuery, className], () => {
    page.value = 1
  })

  // 默认选中第一个班级（与原行为一致）
  const selectFirstClass = () => {
    if (!className.value && classes.value && classes.value.length > 0) {
      className.value = classes.value[0].name
    }
  }
  watch(classes, selectFirstClass, { immediate: true })

  const setSearchQuery = (query: string) => {
    searchQuery.value = query
  }

  const setClassFilter = (name: string) => {
    className.value = name
  }

  return {
    page,
    pageSize,
    searchQuery,
    className,
    isSearching,
    classOptions,
    filteredStudents,
    total,
    totalPages,
    isPending,
    error,
    refetch,
    setSearchQuery,
    setClassFilter,
    selectFirstClass,
  }
}
