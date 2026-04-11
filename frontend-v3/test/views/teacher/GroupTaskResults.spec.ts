/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import GroupTaskResults from '@/views/teacher/GroupTaskResults.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '1' } }),
  useRouter: () => ({ back: vi.fn() }),
}))

vi.mock('@/features/group-collaboration', () => ({
  useTaskResults: () => ({
    data: ref({
      task: { id: 1, title: '任务A', status: 'closed' },
      dimensions: [{ id: 1, name: '创意' }],
      results: {
        1: { group_id: 1, group_name: '第一组', teacher_scores: { '创意': 80 }, peer_scores: { '创意': 70 }, final_scores: { '创意': 76 }, task_final: 76 },
      },
    }),
    isPending: ref(false),
  }),
}))

vi.mock('@/features/group-collaboration/components', () => ({
  JojoRadarChart: { template: '<div class="jojo-radar"></div>' },
}))

const stubs = {
  Card: { template: '<div class="card"><slot /></div>' },
  Badge: { template: '<span class="badge"><slot /></span>' },
  DataContainer: { props: ['loading', 'hasData'], template: '<div class="data-container"><slot /></div>' },
}

describe('GroupTaskResults', () => {
  it('renders without error', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = mount(GroupTaskResults, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })
    expect(wrapper.find('div').exists()).toBe(true)
    expect(wrapper.text()).toContain('任务结果')
  })
})
