/**
 * @vitest-environment jsdom
 *
 * 学生端我的成绩：当前学期选课成绩列表
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import MyGrades from '@/views/student/MyGrades.vue'

vi.mock('@/api/enrollments', () => ({
  enrollmentsApi: {
    getMyEnrollments: vi.fn(),
  },
}))

vi.mock('@/composables/useAuth', () => ({
  useAuthQuery: () => ({ user: ref({ username: 'S001', name: '学生1', role: 'student' }) }),
}))

import { enrollmentsApi } from '@/api/enrollments'
const mockedGetMyEnrollments = vi.mocked(enrollmentsApi.getMyEnrollments)

const MockCard = { template: '<div class="mock-card"><slot /></div>' }

const MockBadge = {
  props: ['variant'],
  template: '<span class="mock-badge"><slot /></span>',
}

const createTestQueryClient = () => new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

const mountComponent = () => {
  const queryClient = createTestQueryClient()
  return mount(MyGrades, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Card: MockCard,
        Badge: MockBadge,
      },
    },
  })
}

describe('MyGrades 我的成绩', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedGetMyEnrollments.mockResolvedValue([
      { enrollment_id: 1, course_id: 1, course_name: '高等数学', teacher_name: '张老师', class_scope: '一班', score: 85, final_score: 90, status: 'enrolled' },
      { enrollment_id: 2, course_id: 2, course_name: '大学英语', teacher_name: '李老师', class_scope: '一班', score: 70, final_score: null, status: 'enrolled' },
    ])
  })

  it('渲染各科成绩（课程/教师/平时/期末）', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(mockedGetMyEnrollments).toHaveBeenCalledWith('S001')
    expect(wrapper.text()).toContain('高等数学')
    expect(wrapper.text()).toContain('张老师')
    expect(wrapper.text()).toContain('85')
    expect(wrapper.text()).toContain('90')
  })

  it('期末成绩未公布时显示占位符', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('—')
  })

  it('无选课时显示空状态', async () => {
    mockedGetMyEnrollments.mockResolvedValue([])
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('暂无选课成绩')
  })
})
