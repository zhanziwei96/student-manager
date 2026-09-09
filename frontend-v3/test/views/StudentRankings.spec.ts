/**
 * @vitest-environment jsdom
 *
 * 学生端排行榜：本班各科个人成绩榜
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import StudentRankings from '@/views/student/StudentRankings.vue'

vi.mock('@/api/rankings', () => ({
  rankingsApi: {
    getRankings: vi.fn(),
  },
}))

vi.mock('@/api/enrollments', () => ({
  enrollmentsApi: {
    getMyEnrollments: vi.fn(() => Promise.resolve([
      { enrollment_id: 1, course_id: 1, course_name: '高等数学', teacher_name: '张老师', class_scope: '一班', score: 85, final_score: null, status: 'enrolled' },
    ])),
  },
}))

vi.mock('@/composables/useAuth', () => ({
  useAuthQuery: () => ({ user: ref({ username: 'S001', name: '学生1', role: 'student' }) }),
}))

import { rankingsApi } from '@/api/rankings'
const mockedGetRankings = vi.mocked(rankingsApi.getRankings)

const MockCard = { template: '<div class="mock-card"><slot /></div>' }

const MockSelect = {
  name: 'Select',
  props: ['modelValue', 'options', 'placeholder'],
  emits: ['update:modelValue'],
  template: `
    <select :value="modelValue" class="mock-select" @change="$emit('update:modelValue', $event.target.value)">
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option v-for="opt in options || []" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
  `,
}

const createTestQueryClient = () => new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

const mountComponent = () => {
  const queryClient = createTestQueryClient()
  return mount(StudentRankings, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Card: MockCard,
        Select: MockSelect,
      },
    },
  })
}

describe('StudentRankings 学生排行榜', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedGetRankings.mockResolvedValue({
      type: 'individual',
      scope: 'class',
      course_name: '高等数学',
      classes: ['一班'],
      entries: [
        { rank: 1, student_id: 'S001', name: '学生1', class_name: '一班', score: 90 },
        { rank: 2, student_id: 'S002', name: '学生2', class_name: '一班', score: 80 },
      ],
      my_rank: { rank: 1, student_id: 'S001', name: '学生1', class_name: '一班', score: 90 },
    })
  })

  it('未选择科目时显示提示', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('请选择科目')
    expect(mockedGetRankings).not.toHaveBeenCalled()
  })

  it('选择科目后查询本班个人榜并高亮自己', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const select = wrapper.find('.mock-select')
    await select.setValue('1')
    await flushPromises()

    expect(mockedGetRankings).toHaveBeenCalledWith({
      type: 'individual', course_id: 1, scope: 'class',
    })
    expect(wrapper.text()).toContain('学生2')
    expect(wrapper.text()).toContain('（我）')
    expect(wrapper.text()).toContain('第 1 名')
  })
})
