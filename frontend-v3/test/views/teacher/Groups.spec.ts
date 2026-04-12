/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Groups from '@/views/teacher/Groups.vue'

// Shared mutable state for mocks
const mockGroupSettingsData = ref<{ class_name: string; max_members_per_group: number } | null>(null)

vi.mock('@/composables', () => ({
  useClasses: () => ({ data: ref([{ name: '计算机1班', status: 'active' }]) }),
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('@/features/group-collaboration', () => ({
  useTeacherGroups: () => ({ data: ref([]), isPending: ref(false) }),
  useAutoAssign: () => ({ mutateAsync: vi.fn(), isPending: ref(false) }),
  useClassGroupSettings: () => ({ data: mockGroupSettingsData }),
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

function createTestQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

describe('Groups', () => {
  beforeEach(() => {
    mockGroupSettingsData.value = null
  })

  it('renders without error', () => {
    const queryClient = createTestQueryClient()
    const wrapper = mount(Groups, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })
    expect(wrapper.find('div').exists()).toBe(true)
    expect(wrapper.text()).toContain('小组管理')
  })

  it('initializes maxMembers from cached groupSettings on mount', async () => {
    // Simulate Vue Query cached data being available synchronously
    mockGroupSettingsData.value = { class_name: '计算机1班', max_members_per_group: 8 }

    const queryClient = createTestQueryClient()
    const wrapper = mount(Groups, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })

    await flushPromises()
    await nextTick()

    const input = wrapper.find('input[type="number"]')
    expect(input.exists()).toBe(true)
    expect((input.element as HTMLInputElement).value).toBe('8')
  })

  it('falls back to default 5 when no groupSettings available', async () => {
    mockGroupSettingsData.value = null

    const queryClient = createTestQueryClient()
    const wrapper = mount(Groups, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })

    await flushPromises()
    await nextTick()

    const input = wrapper.find('input[type="number"]')
    expect(input.exists()).toBe(true)
    expect((input.element as HTMLInputElement).value).toBe('5')
  })
})
