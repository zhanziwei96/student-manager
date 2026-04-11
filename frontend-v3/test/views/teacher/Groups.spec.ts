/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Groups from '@/views/teacher/Groups.vue'

vi.mock('@/composables', () => ({
  useClasses: () => ({ data: ref([{ name: '计算机1班', status: 'active' }]) }),
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('@/features/group-collaboration', () => ({
  useTeacherGroups: () => ({ data: ref([]), isPending: ref(false) }),
  useAutoAssign: () => ({ mutateAsync: vi.fn(), isPending: ref(false) }),
  useClassGroupSettings: () => ({ data: ref(null) }),
  useUpdateClassGroupSettings: () => ({ mutateAsync: vi.fn() }),
}))

vi.mock('@tanstack/vue-query', async () => {
  const actual = await vi.importActual('@tanstack/vue-query')
  return {
    ...(actual as any),
    useQuery: () => ({ data: ref([]), isPending: ref(false) }),
    useMutation: () => ({ mutateAsync: vi.fn() }),
  }
})

const stubs = {
  Card: { template: '<div class="card"><slot /></div>' },
  Button: { props: ['loading', 'disabled', 'variant'], template: '<button class="btn"><slot /></button>' },
  Select: { props: ['modelValue', 'options'], template: '<select class="select"><slot /></select>' },
  Badge: { template: '<span class="badge"><slot /></span>' },
  DataContainer: { props: ['loading', 'hasData'], template: '<div class="data-container"><slot /></div>' },
  Dialog: { props: ['open', 'title'], template: '<div class="dialog"><slot /></div>' },
}

describe('Groups', () => {
  it('renders without error', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = mount(Groups, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })
    expect(wrapper.find('div').exists()).toBe(true)
    expect(wrapper.text()).toContain('小组管理')
  })
})
