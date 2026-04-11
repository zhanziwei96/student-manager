/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import GroupResults from '@/views/student/GroupResults.vue'

vi.mock('@/features/group-collaboration', () => ({
  useMyGroupResults: () => ({
    data: ref([
      {
        task_id: 1,
        title: '任务A',
        status: 'closed',
        teacher_scores: { '创意': 80 },
        peer_scores: { '创意': 70 },
        final_scores: { '创意': 76 },
        task_final: 76,
      },
    ]),
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

describe('GroupResults', () => {
  it('renders without error', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = mount(GroupResults, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })
    expect(wrapper.find('div').exists()).toBe(true)
    expect(wrapper.text()).toContain('成绩单')
  })
})
