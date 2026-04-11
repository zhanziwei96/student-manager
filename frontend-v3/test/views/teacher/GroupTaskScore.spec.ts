/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import GroupTaskScore from '@/views/teacher/GroupTaskScore.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '1' } }),
  useRouter: () => ({ back: vi.fn() }),
}))

vi.mock('@/composables', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('@/features/group-collaboration', () => ({
  useTaskResults: () => ({
    data: ref({
      task: { id: 1, title: '任务A', status: 'evaluating' },
      dimensions: [{ id: 1, name: '创意' }],
      results: {
        1: { group_id: 1, group_name: '第一组' },
      },
    }),
    isPending: ref(false),
  }),
  useSubmitTeacherScore: () => ({ mutateAsync: vi.fn() }),
}))

const stubs = {
  Card: { template: '<div class="card"><slot /></div>' },
  Button: { props: ['loading', 'disabled', 'variant'], template: '<button class="btn"><slot /></button>' },
  Select: { props: ['modelValue', 'options'], template: '<select class="select"><slot /></select>' },
  DataContainer: { props: ['loading', 'hasData'], template: '<div class="data-container"><slot /></div>' },
}

describe('GroupTaskScore', () => {
  it('renders without error', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = mount(GroupTaskScore, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })
    expect(wrapper.find('div').exists()).toBe(true)
    expect(wrapper.text()).toContain('教师评分')
  })
})
