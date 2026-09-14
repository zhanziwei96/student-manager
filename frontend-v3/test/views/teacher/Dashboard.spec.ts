/**
 * @vitest-environment jsdom
 *
 * 教师仪表板：「开始上课」主任务化首屏
 * - 顶部全宽黑按钮（h-14）链接到 /teacher/session
 * - 有进行中课堂时显示次级提示
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Dashboard from '@/views/teacher/Dashboard.vue'

const mockPush = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

// 进行中的课堂列表（各用例可修改）
const hoisted = vi.hoisted(() => ({ sessions: [] as { id: number }[] }))

vi.mock('@/composables', async () => {
  const { ref } = await import('vue')
  return {
    useStats: () => ({
      data: ref({ total_students: 42 }),
      isPending: ref(false),
      error: ref(null),
    }),
    useTodaySchedules: () => ({
      data: ref([]),
      isPending: ref(false),
    }),
    useActiveClassSessions: () => ({
      data: ref(hoisted.sessions),
    }),
  }
})

const MockCard = { template: '<div class="mock-card"><slot /></div>' }
const MockDataContainer = { template: '<div class="mock-data-container"><slot /></div>' }

const createTestQueryClient = () => new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

const mountComponent = () => {
  const queryClient = createTestQueryClient()
  return mount(Dashboard, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: { Card: MockCard, DataContainer: MockDataContainer },
    },
  })
}

describe('Teacher Dashboard - 开始上课主任务化', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    hoisted.sessions.length = 0
  })

  it('「开始上课」为全宽 h-14 黑按钮，点击跳转 /teacher/session', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const startButton = wrapper.findAll('button').find((b) => b.text().includes('开始上课'))
    expect(startButton).toBeTruthy()
    expect(startButton!.classes()).toContain('h-14')
    expect(startButton!.classes()).toContain('w-full')
    expect(startButton!.classes()).toContain('bg-black')
    expect(startButton!.classes()).toContain('rounded-full')

    await startButton!.trigger('click')
    expect(mockPush).toHaveBeenCalledWith('/teacher/session')
  })

  it('「开始上课」渲染在今日课表与统计卡片之前', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const text = wrapper.text()
    const startIdx = text.indexOf('开始上课')
    const scheduleIdx = text.indexOf('今日课表')
    const statsIdx = text.indexOf('我的学生')
    expect(startIdx).toBeGreaterThanOrEqual(0)
    expect(scheduleIdx).toBeGreaterThan(startIdx)
    expect(statsIdx).toBeGreaterThan(scheduleIdx)
  })

  it('有进行中课堂时显示次级提示并链接到课堂管理', async () => {
    hoisted.sessions.push({ id: 1 }, { id: 2 })
    const wrapper = mountComponent()
    await flushPromises()

    const hint = wrapper.findAll('button').find((b) => b.text().includes('当前有 2 个进行中的课堂'))
    expect(hint).toBeTruthy()
    expect(hint!.classes()).toContain('min-h-[44px]')

    await hint!.trigger('click')
    expect(mockPush).toHaveBeenCalledWith('/teacher/session')
  })

  it('无进行中课堂时不显示次级提示', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).not.toContain('进行中的课堂')
  })
})
