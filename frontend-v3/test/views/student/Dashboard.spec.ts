/**
 * @vitest-environment jsdom
 *
 * 学生仪表板：个人信息 + 我的课程概览 + 我的小组 + 快捷入口
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Dashboard from '@/views/student/Dashboard.vue'

const mockPush = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

vi.mock('@/stores', () => ({
  useAuthStore: () => ({ user: ref({ name: '学生1', role: 'student' }) }),
}))

vi.mock('@/composables/useStudentProfile', () => ({
  useStudentProfile: () => ({
    data: ref({
      student_id: 'S001',
      name: '学生1',
      class_name: '一班',
      is_account_enabled: true,
    }),
    isPending: ref(false),
    error: ref(null),
  }),
}))

vi.mock('@/api/enrollments', () => ({
  enrollmentsApi: {
    getMyEnrollments: vi.fn(),
  },
}))

vi.mock('@/api/groups', () => ({
  groupsApi: {
    getMyGroups: vi.fn(),
  },
}))

import { enrollmentsApi } from '@/api/enrollments'
import { groupsApi } from '@/api/groups'
const mockedEnrollments = vi.mocked(enrollmentsApi.getMyEnrollments)
const mockedMyGroups = vi.mocked(groupsApi.getMyGroups)

const MockCard = { template: '<div class="mock-card"><slot /></div>' }

const createTestQueryClient = () => new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

const mountComponent = () => {
  const queryClient = createTestQueryClient()
  return mount(Dashboard, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: { Card: MockCard },
    },
  })
}

describe('Student Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedEnrollments.mockResolvedValue([
      { enrollment_id: 1, course_id: 1, course_name: '高等数学', teacher_name: '张老师', class_scope: '一班', score: 85, final_score: 90, status: 'enrolled' },
    ])
    mockedMyGroups.mockResolvedValue([
      { id: 1, name: '数学一组', class_name: '一班', course_id: 1, course_name: '高等数学', score: 12, leader_student_id: 'S001', is_leader: true, members: [], pending_requests: [] },
    ])
  })

  it('renders dashboard title and student info', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('学生仪表板')
    expect(wrapper.text()).toContain('一班')
    expect(wrapper.text()).toContain('S001')
  })

  it('展示我的课程（平时/期末）', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('高等数学')
    expect(wrapper.text()).toContain('张老师')
    expect(wrapper.text()).toContain('85')
    expect(wrapper.text()).toContain('90')
  })

  it('展示我的小组累计分', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('数学一组')
    expect(wrapper.text()).toContain('12')
  })

  it('无课程时显示空状态', async () => {
    mockedEnrollments.mockResolvedValue([])
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('暂无选课成绩')
  })

  it('排行榜快捷入口可跳转', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const rankButton = wrapper.findAll('button').find((b) => b.text().includes('查看排行榜'))
    expect(rankButton).toBeTruthy()
    await rankButton!.trigger('click')

    expect(mockPush).toHaveBeenCalledWith('/student/rankings')
  })
})
