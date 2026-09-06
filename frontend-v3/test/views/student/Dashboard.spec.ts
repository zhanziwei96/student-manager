/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Dashboard from '@/views/student/Dashboard.vue'

// Mock auth store
vi.mock('@/stores', () => ({
  useAuthStore: () => ({
    user: { id: 'S001', name: '张三', role: 'student' }
  })
}))

// Mock composables
vi.mock('@/composables/useStudentProfile', () => ({
  useStudentProfile: () => ({
    data: ref({
      id: 1,
      student_id: 'S001',
      name: '张三',
      class_name: '一班',
      score: 88,
      is_account_enabled: true
    }),
    isPending: ref(false),
    error: ref(null)
  })
}))

vi.mock('@/composables', () => ({
  useStudentScoreLogs: () => holder.scoreLogs,
}))

// 排行榜 mock：myRank 由 holder 控制，便于各用例切换有名次/无名次场景
const holder = vi.hoisted(() => ({
  myRank: null as null | { rank: number; student_id: string; name: string; score: number },
  scoreLogs: null as unknown as Record<string, unknown>,
}))

/** 构造 useStudentScoreLogs 的 mock 返回值（各用例可覆盖字段） */
const makeScoreLogs = (overrides: Record<string, unknown> = {}) => ({
  logs: ref([]),
  isPending: ref(false),
  isLoadingMore: ref(false),
  hasMore: ref(false),
  error: ref(null),
  loadMore: vi.fn(),
  ...overrides,
})

vi.mock('@/composables/useLeaderboard', async () => {
  const { computed } = await import('vue')
  return {
    useLeaderboard: () => ({
      data: computed(() => null),
      isPending: computed(() => false),
      error: computed(() => null),
      refetch: vi.fn(),
      students: computed(() => []),
      myRank: computed(() => holder.myRank),
      total: computed(() => 0)
    })
  }
})

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  })

  return mount(Dashboard, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: ['RouterLink']
    }
  })
}

describe('Student Dashboard', () => {
  beforeEach(() => {
    holder.myRank = { rank: 2, student_id: 'S001', name: '张三', score: 999 }
    holder.scoreLogs = makeScoreLogs()
  })

  it('renders dashboard title', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('学生仪表板')
  })

  it('displays student score', async () => {
    const wrapper = createWrapper()
    await flushPromises()
    expect(wrapper.text()).toContain('88')
  })

  it('shows rank badge', async () => {
    const wrapper = createWrapper()
    await flushPromises()
    expect(wrapper.text()).toContain('排名')
  })

  it('displays rank from leaderboard my_rank', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const rankButton = wrapper.findAll('button').find(b => b.text().includes('排名'))
    expect(rankButton?.text()).toContain('第 2 名')
  })

  it('does not display score from leaderboard my_rank', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    // 排行榜 my_rank 中的分数（999）不应出现在 Dashboard 上（只显示名次）
    expect(wrapper.text()).not.toContain('999')
  })

  it('shows placeholder when my_rank is null', async () => {
    holder.myRank = null
    const wrapper = createWrapper()
    await flushPromises()

    const rankButton = wrapper.findAll('button').find(b => b.text().includes('排名'))
    expect(rankButton?.text()).toMatch(/排名\s*-/)
  })

  it('has leaderboard entry button', async () => {
    const wrapper = createWrapper()
    await flushPromises()
    expect(wrapper.text()).toContain('查看排行榜')
  })

  it('rank badge is clickable', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    // 查找包含"排名"文本的按钮元素
    const buttons = wrapper.findAll('button')
    const hasRankBadge = buttons.some(el => el.text().includes('排名'))
    expect(hasRankBadge).toBe(true)
  })

  it('leaderboard button is clickable', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    // 查找包含"查看排行榜"文本的按钮元素
    const buttons = wrapper.findAll('button')
    const hasLeaderboardButton = buttons.some(el => el.text().includes('查看排行榜'))
    expect(hasLeaderboardButton).toBe(true)
  })
})

describe('Student Dashboard - 分数日志加载更多', () => {
  const fakeLog = (id: number) => ({
    id,
    student_id: 'S001',
    delta: 2,
    reason: `加分${id}`,
    operator: '老师',
    old_score: 80,
    new_score: 82,
    created_at: '2026-09-01T08:00:00',
  })

  beforeEach(() => {
    holder.myRank = null
  })

  it('hasMore 为 true 时显示"加载更多"按钮', async () => {
    holder.scoreLogs = makeScoreLogs({
      logs: ref([fakeLog(1)]),
      hasMore: ref(true),
    })
    const wrapper = createWrapper()
    await flushPromises()

    const btn = wrapper.find('[data-testid="load-more-logs"]')
    expect(btn.exists()).toBe(true)
    expect(btn.text()).toContain('加载更多')
  })

  it('点击"加载更多"调用 loadMore', async () => {
    const loadMore = vi.fn()
    holder.scoreLogs = makeScoreLogs({
      logs: ref([fakeLog(1)]),
      hasMore: ref(true),
      loadMore,
    })
    const wrapper = createWrapper()
    await flushPromises()

    await wrapper.find('[data-testid="load-more-logs"]').trigger('click')
    expect(loadMore).toHaveBeenCalled()
  })

  it('hasMore 为 false 时隐藏"加载更多"按钮', async () => {
    holder.scoreLogs = makeScoreLogs({
      logs: ref([fakeLog(1)]),
      hasMore: ref(false),
    })
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.find('[data-testid="load-more-logs"]').exists()).toBe(false)
  })

  it('加载中时按钮禁用并显示加载文案', async () => {
    holder.scoreLogs = makeScoreLogs({
      logs: ref([fakeLog(1)]),
      hasMore: ref(true),
      isLoadingMore: ref(true),
    })
    const wrapper = createWrapper()
    await flushPromises()

    const btn = wrapper.find('[data-testid="load-more-logs"]')
    expect(btn.attributes('disabled')).toBeDefined()
    expect(btn.text()).toContain('加载中')
  })

  it('无日志时不显示"加载更多"按钮', async () => {
    holder.scoreLogs = makeScoreLogs({
      logs: ref([]),
      hasMore: ref(true),
    })
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.find('[data-testid="load-more-logs"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('暂无分数变更记录')
  })
})
