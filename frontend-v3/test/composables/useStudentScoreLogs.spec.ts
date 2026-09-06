/**
 * @vitest-environment jsdom
 *
 * useStudentScoreLogs - 分数日志"加载更多"分页 composable 测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref, h, defineComponent, nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { useStudentScoreLogs } from '@/composables/useStudentScoreLogs'
import { studentsApi } from '@/api/students'
import type { ScoreLog } from '@/types'

vi.mock('@/api/students', () => ({
  studentsApi: {
    getScoreLogs: vi.fn(),
  },
}))

const mockedGetScoreLogs = vi.mocked(studentsApi.getScoreLogs)

const fakeLog = (id: number): ScoreLog => ({
  id,
  student_id: 'S001',
  delta: 2,
  reason: `加分${id}`,
  operator: '老师',
  old_score: 80,
  new_score: 82,
  created_at: '2026-09-01T08:00:00',
} as ScoreLog)

// 在 Vue setup 上下文中运行 composable（本 composable 不含 useQuery，无需 QueryClient）
function withSetup<T>(composable: () => T): { result: T; unmount: () => void } {
  let result!: T
  const TestComponent = defineComponent({
    setup() {
      result = composable()
      return () => h('div')
    },
  })
  const wrapper = mount(TestComponent)
  return { result, unmount: () => wrapper.unmount() }
}

describe('useStudentScoreLogs', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('studentId 就绪后自动加载第一页（limit=pageSize, offset=0）', async () => {
    mockedGetScoreLogs.mockResolvedValue([fakeLog(1), fakeLog(2)])
    const { result, unmount } = withSetup(() => useStudentScoreLogs('S001', { pageSize: 2 }))
    await flushPromises()

    expect(mockedGetScoreLogs).toHaveBeenCalledWith('S001', { limit: 2, offset: 0 })
    expect(result.logs.value.map((l) => l.id)).toEqual([1, 2])
    // 返回数量 == pageSize，认为可能还有更多
    expect(result.hasMore.value).toBe(true)
    unmount()
  })

  it('loadMore 追加下一页（offset 累加）', async () => {
    mockedGetScoreLogs
      .mockResolvedValueOnce([fakeLog(1), fakeLog(2)])
      .mockResolvedValueOnce([fakeLog(3)])

    const { result, unmount } = withSetup(() => useStudentScoreLogs('S001', { pageSize: 2 }))
    await flushPromises()

    await result.loadMore()

    expect(mockedGetScoreLogs).toHaveBeenNthCalledWith(2, 'S001', { limit: 2, offset: 2 })
    expect(result.logs.value.map((l) => l.id)).toEqual([1, 2, 3])
    // 第二页返回数量 < pageSize，没有更多了
    expect(result.hasMore.value).toBe(false)
    unmount()
  })

  it('hasMore 为 false 后 loadMore 不再请求', async () => {
    mockedGetScoreLogs.mockResolvedValue([fakeLog(1)])
    const { result, unmount } = withSetup(() => useStudentScoreLogs('S001', { pageSize: 2 }))
    await flushPromises()

    expect(result.hasMore.value).toBe(false)
    await result.loadMore()
    expect(mockedGetScoreLogs).toHaveBeenCalledTimes(1)
    unmount()
  })

  it('studentId 变化时重置并重新加载', async () => {
    mockedGetScoreLogs.mockResolvedValue([fakeLog(1)])
    const studentId = ref('S001')
    const { result, unmount } = withSetup(() => useStudentScoreLogs(studentId, { pageSize: 2 }))
    await flushPromises()

    studentId.value = 'S002'
    await nextTick()
    await flushPromises()

    expect(mockedGetScoreLogs).toHaveBeenLastCalledWith('S002', { limit: 2, offset: 0 })
    expect(result.logs.value.map((l) => l.id)).toEqual([1])
    unmount()
  })

  it('studentId 为空时不发请求', async () => {
    const { unmount } = withSetup(() => useStudentScoreLogs(''))
    await flushPromises()

    expect(mockedGetScoreLogs).not.toHaveBeenCalled()
    unmount()
  })
})
