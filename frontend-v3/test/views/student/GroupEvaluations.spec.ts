/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import GroupEvaluations from '@/views/student/GroupEvaluations.vue'

const mockTasks = ref<any[]>([{ id: 1, title: '任务A', status: 'evaluating', class_name: '计算机1班' }])
const mockTasksPending = ref(false)
const mockEvaluations = ref<any[]>([
  {
    target_group_id: 2,
    target_group_name: '第二组',
    dimensions: [{ id: 1, name: '创意', scored: false }],
    all_scored: false,
  },
])
const mockEvaluationsPending = ref(false)

vi.mock('@/composables', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('@/features/group-collaboration', () => ({
  useStudentGroupTasks: () => ({
    data: mockTasks,
    isPending: mockTasksPending,
  }),
  useEvaluations: () => ({
    data: mockEvaluations,
    isPending: mockEvaluationsPending,
  }),
  useSubmitStudentScores: () => ({ mutateAsync: vi.fn(), isPending: ref(false) }),
}))

const stubs = {
  Card: { template: '<div class="card"><slot /></div>' },
  Button: { props: ['loading', 'disabled', 'variant'], template: '<button class="btn"><slot /></button>' },
  Select: { props: ['modelValue', 'options'], template: '<select class="select"><slot /></select>' },
  Badge: { template: '<span class="badge"><slot /></span>' },
  DataContainer: { props: ['loading', 'hasData', 'emptyText'], template: '<div class="data-container"><slot /></div>' },
}

describe('GroupEvaluations', () => {
  beforeEach(() => {
    mockTasks.value = [{ id: 1, title: '任务A', status: 'evaluating', class_name: '计算机1班' }]
    mockTasksPending.value = false
    mockEvaluations.value = [
      {
        target_group_id: 2,
        target_group_name: '第二组',
        dimensions: [{ id: 1, name: '创意', scored: false }],
        all_scored: false,
      },
    ]
    mockEvaluationsPending.value = false
  })

  it('renders without error', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = mount(GroupEvaluations, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })
    expect(wrapper.find('div').exists()).toBe(true)
    expect(wrapper.text()).toContain('组间互评')
  })

  it('shows loading when tasks are loading', async () => {
    mockTasksPending.value = true
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = mount(GroupEvaluations, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })
    await nextTick()
    const container = wrapper.findComponent(stubs.DataContainer)
    expect(container.props('loading')).toBe(true)
  })

  it('shows empty state with correct text when student has no tasks', async () => {
    mockTasks.value = []
    mockEvaluations.value = []
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = mount(GroupEvaluations, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })
    await nextTick()
    const container = wrapper.findComponent(stubs.DataContainer)
    expect(container.props('hasData')).toBe(false)
    expect(container.props('emptyText')).toBe('暂无任务')
  })
})
