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
  useStudentScoreLogs: () => ({
    data: ref([]),
    isPending: ref(false)
  })
}))

// 排行榜 mock：myRank 由 holder 控制，便于各用例切换有名次/无名次场景
const holder = vi.hoisted(() => ({
  myRank: null as null | { rank: number; student_id: string; name: string; score: number }
}))

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
