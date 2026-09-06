/**
 * @vitest-environment jsdom
 *
 * usePaginatedStudents - 学生列表分页 composable 测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { h, defineComponent, nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import { usePaginatedStudents } from '@/features/students/composables/usePaginatedStudents'
import { studentsApi } from '@/api'
import { classesApi } from '@/api/classes'

vi.mock('@/api', () => ({
  studentsApi: {
    getPaginated: vi.fn(),
  },
}))

vi.mock('@/api/classes', () => ({
  classesApi: {
    getAll: vi.fn(),
  },
}))

const mockedGetPaginated = vi.mocked(studentsApi.getPaginated)
const mockedGetClasses = vi.mocked(classesApi.getAll)

// 在 Vue setup 上下文中运行 composable
function withSetup<T>(composable: () => T): { result: T; unmount: () => void } {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
    },
  })

  let result!: T
  const TestComponent = defineComponent({
    setup() {
      result = composable()
      return () => h('div')
    },
  })

  const wrapper = mount(TestComponent, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
    },
  })

  return { result, unmount: () => wrapper.unmount() }
}

const fakeStudent = (id: string, name: string, className = '一班') => ({
  student_id: id,
  name,
  class_name: className,
  score: 80,
  is_account_enabled: true,
  checkin_status: 'not_checked_in' as const,
})

describe('usePaginatedStudents', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedGetClasses.mockResolvedValue([{ name: '一班', status: 'inactive' }, { name: '二班', status: 'inactive' }])
    mockedGetPaginated.mockResolvedValue({
      items: [fakeStudent('S001', '张三')],
      total: 120,
    })
  })

  it('默认以 limit=pageSize, offset=0 请求第一页', async () => {
    const { unmount } = withSetup(() => usePaginatedStudents(50))
    await flushPromises()

    // 默认选中第一个班级后按该班级请求
    expect(mockedGetPaginated).toHaveBeenCalledWith({
      class_name: '一班',
      limit: 50,
      offset: 0,
    })
    unmount()
  })

  it('翻页后 offset 随之变化', async () => {
    const { result, unmount } = withSetup(() => usePaginatedStudents(50))
    await flushPromises()
    mockedGetPaginated.mockClear()

    result.page.value = 3
    await flushPromises()

    expect(mockedGetPaginated).toHaveBeenCalledWith({
      class_name: '一班',
      limit: 50,
      offset: 100,
    })
    unmount()
  })

  it('totalPages 由服务端 total 计算', async () => {
    const { result, unmount } = withSetup(() => usePaginatedStudents(50))
    await flushPromises()

    expect(result.total.value).toBe(120)
    expect(result.totalPages.value).toBe(3)
    unmount()
  })

  it('切换班级时回到第一页并按新班级请求', async () => {
    const { result, unmount } = withSetup(() => usePaginatedStudents(50))
    await flushPromises()

    result.page.value = 2
    await nextTick()
    mockedGetPaginated.mockClear()

    result.setClassFilter('二班')
    await flushPromises()

    expect(result.page.value).toBe(1)
    expect(mockedGetPaginated).toHaveBeenCalledWith({
      class_name: '二班',
      limit: 50,
      offset: 0,
    })
    unmount()
  })

  it('搜索模式：拉取全量（不带 limit/offset）并前端过滤', async () => {
    mockedGetPaginated.mockResolvedValue({
      items: [
        fakeStudent('S001', '张三'),
        fakeStudent('S002', '李四'),
        fakeStudent('S101', '张小三'),
      ],
      total: 3,
    })
    const { result, unmount } = withSetup(() => usePaginatedStudents(50))
    await flushPromises()
    mockedGetPaginated.mockClear()

    result.setSearchQuery('张')
    await flushPromises()

    // 搜索请求不带分页参数
    expect(mockedGetPaginated).toHaveBeenCalledWith({
      class_name: '一班',
      limit: undefined,
      offset: undefined,
    })
    // 前端过滤：姓名/学号匹配
    expect(result.isSearching.value).toBe(true)
    expect(result.filteredStudents.value.map((s) => s.student_id)).toEqual(['S001', 'S101'])
    unmount()
  })

  it('清空搜索后恢复分页视图（缓存命中，不重复请求）', async () => {
    const { result, unmount } = withSetup(() => usePaginatedStudents(50))
    await flushPromises()

    result.setSearchQuery('张')
    await flushPromises()
    mockedGetPaginated.mockClear()

    result.setSearchQuery('')
    await flushPromises()

    expect(result.isSearching.value).toBe(false)
    // 分页 key 与初始相同且在 staleTime 内，直接命中缓存，不发新请求
    expect(mockedGetPaginated).not.toHaveBeenCalled()
    expect(result.filteredStudents.value.map((s) => s.student_id)).toEqual(['S001'])
    unmount()
  })

  it('班级选项来自 /classes 接口', async () => {
    const { result, unmount } = withSetup(() => usePaginatedStudents(50))
    await flushPromises()

    expect(mockedGetClasses).toHaveBeenCalled()
    expect(result.classOptions.value.map((o) => o.value)).toEqual(['', '一班', '二班'])
    unmount()
  })
})
