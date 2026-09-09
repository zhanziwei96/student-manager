/**
 * @vitest-environment jsdom
 *
 * 学生端我的小组：多科小组（课程维度）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import { createPinia, setActivePinia } from 'pinia'
import MyGroup from '@/views/student/MyGroup.vue'

// Shared mutable state for mocks
const mockMyGroups = ref<any[]>([])
const mockCourses = ref<any[]>([])
const mockCreateGroup = vi.fn()

vi.mock('@/composables', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('@/features/group-collaboration', () => ({
  useMyGroups: () => ({ data: mockMyGroups, isPending: ref(false) }),
  useStudentGroups: () => ({ data: ref([]), isPending: ref(false) }),
  useCreateGroup: () => ({ mutateAsync: mockCreateGroup }),
  useJoinGroup: () => ({ mutateAsync: vi.fn(), isPending: ref(false) }),
  useApproveJoin: () => ({ mutateAsync: vi.fn() }),
}))

vi.mock('@/api/courses', () => ({
  coursesApi: {
    list: vi.fn(),
  },
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

import { coursesApi } from '@/api/courses'

const fakeGroup = (id: number, courseId: number, courseName: string) => ({
  id,
  name: `第${id}组`,
  class_name: '计算机1班',
  course_id: courseId,
  course_name: courseName,
  score: 10,
  leader_student_id: '2021001',
  leader_name: '测试学生',
  is_leader: true,
  members: [{ student_id: '2021001', name: '测试学生' }],
  pending_requests: [],
})

const stubs = {
  Card: { template: '<div class="card"><slot /></div>' },
  Button: { props: ['loading', 'disabled', 'variant'], emits: ['click'], template: '<button class="btn" @click="$emit(\'click\')"><slot /></button>' },
  Badge: { template: '<span class="badge"><slot /></span>' },
  Select: { props: ['modelValue', 'options', 'placeholder'], emits: ['update:modelValue'], template: '<select class="select"><slot /></select>' },
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
    mockMyGroups.value = [fakeGroup(1, 1, '高等数学')]
    mockCourses.value = [{ id: 1, code: 'MATH1', name: '高等数学', department: '', status: 'active' }]
    vi.mocked(coursesApi.list).mockResolvedValue(mockCourses.value)
    mockCreateGroup.mockReset()
  })

  it('renders without error', async () => {
    const wrapper = mountMyGroup()
    await flushPromises()

    expect(wrapper.text()).toContain('我的小组')
    expect(wrapper.text()).toContain('第1组')
  })

  it('显示小组课程与小组分', async () => {
    const wrapper = mountMyGroup()
    await flushPromises()

    expect(wrapper.text()).toContain('高等数学')
    expect(wrapper.text()).toContain('10')
  })

  it('create dialog includes course selector', async () => {
    // 无小组时展示"创建小组"入口
    mockMyGroups.value = []

    const wrapper = mountMyGroup()
    await flushPromises()

    const createBtn = wrapper.findAll('button').find((b) => b.text().includes('创建小组'))
    expect(createBtn).toBeTruthy()
    await createBtn!.trigger('click')
    await flushPromises()

    const dialog = wrapper.find('.dialog')
    expect(dialog.exists()).toBe(true)
    expect(dialog.text()).toContain('课程')
    expect(dialog.find('select').exists()).toBe(true)
  })
})
