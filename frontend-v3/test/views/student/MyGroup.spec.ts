/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import { createPinia, setActivePinia } from 'pinia'
import MyGroup from '@/views/student/MyGroup.vue'

// Shared mutable state for mocks
const mockMyGroup = ref<any | null>({
  id: 1,
  name: '第一组',
  class_name: '计算机1班',
  leader_student_id: '2021001',
  is_leader: true,
  members: [{ student_id: '2021001' }],
  pending_requests: [],
})
const mockSubjectsData = ref<any[]>([])
const mockCreateGroup = vi.fn()

vi.mock('@/composables', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
  useSubjects: () => ({ data: mockSubjectsData }),
}))

vi.mock('@/features/group-collaboration', () => ({
  useMyGroup: () => ({ data: mockMyGroup, isPending: ref(false) }),
  useStudentGroups: () => ({ data: ref([]), isPending: ref(false) }),
  useCreateGroup: () => ({ mutateAsync: mockCreateGroup }),
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
  Select: { props: ['modelValue', 'options'], template: '<select class="select"><slot /></select>' },
  Label: { template: '<label class="label"><slot /></label>' },
  DataContainer: { props: ['loading', 'hasData'], template: '<div class="data-container"><slot /></div>' },
  Dialog: {
    props: ['open', 'title'],
    template: '<div v-if="open" class="dialog"><div class="dialog-title">{{ title }}</div><slot /><slot name="footer" /></div>',
  },
}

function mountMyGroup() {
  setActivePinia(createPinia())
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return mount(MyGroup, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs,
    },
  })
}

describe('MyGroup', () => {
  beforeEach(() => {
    mockMyGroup.value = {
      id: 1,
      name: '第一组',
      class_name: '计算机1班',
      leader_student_id: '2021001',
      is_leader: true,
      members: [{ student_id: '2021001' }],
      pending_requests: [],
    }
    mockSubjectsData.value = []
    mockCreateGroup.mockReset()
  })

  it('renders without error', () => {
    const wrapper = mountMyGroup()
    expect(wrapper.find('div').exists()).toBe(true)
    expect(wrapper.text()).toContain('我的小组')
  })

  it('create dialog includes subject selector', async () => {
    // 无小组时展示“创建小组”入口
    mockMyGroup.value = null
    mockSubjectsData.value = [{ id: 1, name: '数学', semester: '2026-2027-1' }]

    const wrapper = mountMyGroup()

    const createBtn = wrapper.findAll('button').find((b) => b.text().includes('创建小组'))
    expect(createBtn).toBeTruthy()
    await createBtn!.trigger('click')

    const dialog = wrapper.find('.dialog')
    expect(dialog.exists()).toBe(true)
    expect(dialog.text()).toContain('科目')
    expect(dialog.find('select').exists()).toBe(true)
  })
})
