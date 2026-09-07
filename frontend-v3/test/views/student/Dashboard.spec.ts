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

// 科目数据 mock：subjects / subjectRanks / subjectLogs 由 holder 控制，便于各用例切换场景
const holder = vi.hoisted(() => ({
  subjects: [] as Array<{
    subject_id: number
    subject_name: string
    teacher_id: number
    teacher_name: string
    score: number
  }>,
  subjectRanks: {} as Record<number, { rank: number; student_id: string; name: string; score: number } | null>,
  subjectLogs: [] as Array<Record<string, unknown>>,
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

// Mock 学生科目分数 API
vi.mock('@/api/students', () => ({
  studentsApi: {
    getSubjects: () => Promise.resolve(holder.subjects),
  },
}))

// Mock lib/api 的 get：排行榜（按科目）与科目分数历史都走它
vi.mock('@/lib/api', () => ({
  get: (url: string, params?: Record<string, unknown>) => {
    if (url === '/students/leaderboard') {
      const subjectId = params?.subject_id as number
      return Promise.resolve({
        scope: 'class',
        students: [],
        total: 0,
        my_rank: holder.subjectRanks[subjectId] ?? null,
      })
    }
    if (url.endsWith('/logs')) {
      return Promise.resolve(holder.subjectLogs)
    }
    return Promise.resolve(null)
  },
}))

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
    holder.subjects = [
      { subject_id: 1, subject_name: '数学', teacher_id: 1, teacher_name: '王老师', score: 90 },
      { subject_id: 2, subject_name: '语文', teacher_id: 2, teacher_name: '李老师', score: 85 },
    ]
    holder.subjectRanks = {
      1: { rank: 3, student_id: 'S001', name: '张三', score: 999 },
      2: null,
    }
    holder.subjectLogs = []
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

  it('has leaderboard entry button', async () => {
    const wrapper = createWrapper()
    await flushPromises()
    expect(wrapper.text()).toContain('查看排行榜')
  })

  it('leaderboard button is clickable', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    // 查找包含"查看排行榜"文本的按钮元素
    const buttons = wrapper.findAll('button')
    const hasLeaderboardButton = buttons.some(el => el.text().includes('查看排行榜'))
    expect(hasLeaderboardButton).toBe(true)
  })

  it('shows subject cards', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    // 显示多个科目卡片：科目名 + 分数 + 任课教师
    expect(wrapper.text()).toContain('我的科目')
    expect(wrapper.find('[data-testid="subject-card-1"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="subject-card-2"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('数学')
    expect(wrapper.text()).toContain('语文')
    expect(wrapper.text()).toContain('王老师')
    expect(wrapper.text()).toContain('90')
    expect(wrapper.text()).toContain('85')
  })

  it('shows subject rank from leaderboard my_rank', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const card = wrapper.find('[data-testid="subject-card-1"]')
    expect(card.text()).toContain('第 3 名')
  })

  it('does not display score from leaderboard my_rank', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    // 科目排行榜 my_rank 中的分数（999）不应出现在 Dashboard 上（只显示名次）
    expect(wrapper.text()).not.toContain('999')
  })

  it('shows placeholder when subject rank is null', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const card = wrapper.find('[data-testid="subject-card-2"]')
    expect(card.text()).toContain('暂无排名')
  })

  it('shows empty state when no subjects', async () => {
    holder.subjects = []
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.find('[data-testid="subject-cards"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('暂无科目分数')
  })

  it('expands subject score history on card click', async () => {
    holder.subjectLogs = [
      {
        old_score: 80,
        new_score: 90,
        delta: 10,
        reason: '考试加分',
        operator: '王老师',
        created_at: '2026-09-01T08:00:00',
      },
    ]
    const wrapper = createWrapper()
    await flushPromises()

    // 展开前不显示分数历史面板
    expect(wrapper.find('[data-testid="subject-logs-panel"]').exists()).toBe(false)

    await wrapper.find('[data-testid="subject-card-1"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="subject-logs-panel"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('考试加分')
    expect(wrapper.text()).toContain('+10')
  })

  it('collapses subject score history on second click', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    await wrapper.find('[data-testid="subject-card-1"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="subject-logs-panel"]').exists()).toBe(true)

    await wrapper.find('[data-testid="subject-card-1"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="subject-logs-panel"]').exists()).toBe(false)
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
    holder.subjects = []
    holder.subjectLogs = []
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
