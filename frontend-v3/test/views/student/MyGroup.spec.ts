/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import { createPinia, setActivePinia } from 'pinia'
import MyGroup from '@/views/student/MyGroup.vue'

vi.mock('@/composables', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('@/features/group-collaboration', () => ({
  useMyGroup: () => ({
    data: ref({
      id: 1,
      name: '第一组',
      class_name: '计算机1班',
      leader_student_id: '2021001',
      is_leader: true,
      members: [{ student_id: '2021001' }],
      pending_requests: [],
    }),
    isPending: ref(false),
  }),
  useStudentGroups: () => ({ data: ref([]), isPending: ref(false) }),
  useCreateGroup: () => ({ mutateAsync: vi.fn() }),
  useJoinGroup: () => ({ mutateAsync: vi.fn(), isPending: ref(false) }),
  useApproveJoin: () => ({ mutateAsync: vi.fn() }),
}))

vi.mock('@/stores', () => ({
  useAuthStore: () => ({
    user: ref({ id: '2021001', name: '测试学生', role: 'student', class_name: '计算机1班' }),
  }),
}))

vi.mock('@tanstack/vue-query', async () => {
  const actual = await vi.importActual('@tanstack/vue-query')
  return {
    ...(actual as any),
    useMutation: () => ({ mutateAsync: vi.fn() }),
  }
})

const stubs = {
  Card: { template: '<div class="card"><slot /></div>' },
  Button: { props: ['loading', 'disabled', 'variant'], template: '<button class="btn"><slot /></button>' },
  Badge: { template: '<span class="badge"><slot /></span>' },
  DataContainer: { props: ['loading', 'hasData'], template: '<div class="data-container"><slot /></div>' },
  Dialog: { props: ['open', 'title'], template: '<div class="dialog"><slot /></div>' },
}

describe('MyGroup', () => {
  it('renders without error', () => {
    setActivePinia(createPinia())
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = mount(MyGroup, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })
    expect(wrapper.find('div').exists()).toBe(true)
    expect(wrapper.text()).toContain('我的小组')
  })
})
