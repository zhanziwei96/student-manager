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
  useStudents: () => ({
    data: ref([
      { id: 1, student_id: 'S001', name: '张三', score: 88 },
      { id: 2, student_id: 'S002', name: '李四', score: 95 }
    ])
  }),
  useStudentScoreLogs: () => ({
    data: ref([]),
    isPending: ref(false)
  })
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

  it('has leaderboard entry button', async () => {
    const wrapper = createWrapper()
    await flushPromises()
    expect(wrapper.text()).toContain('查看排行榜')
  })

  it('rank badge is clickable', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const clickableElements = wrapper.findAll('.cursor-pointer')
    const hasRankBadge = clickableElements.some(el => el.text().includes('排名'))
    expect(hasRankBadge).toBe(true)
  })

  it('leaderboard button is clickable', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const clickableElements = wrapper.findAll('.cursor-pointer')
    const hasLeaderboardButton = clickableElements.some(el => el.text().includes('查看排行榜'))
    expect(hasLeaderboardButton).toBe(true)
  })
})
