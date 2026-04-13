/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import GroupTasks from '@/views/teacher/GroupTasks.vue'

const teacherGroupTasksMock = vi.hoisted(() => {
  const { ref } = require('vue')
  return {
    data: ref([]),
    isPending: ref(false),
  }
})

vi.mock('@/composables', () => ({
  useClasses: () => ({ data: ref([{ name: '计算机1班', status: 'active' }]), isPending: ref(false) }),
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('@/features/group-collaboration', () => ({
  useTeacherGroupTasks: () => teacherGroupTasksMock,
  useCreateGroupTask: () => ({ mutateAsync: vi.fn(), isPending: ref(false) }),
  useStartGroupTask: () => ({ mutateAsync: vi.fn() }),
  useCloseGroupTask: () => ({ mutateAsync: vi.fn() }),
  useCloneGroupTask: () => ({ mutateAsync: vi.fn() }),
}))

const stubs = {
  Card: { template: '<div class="card"><slot /></div>' },
  Button: { props: ['loading', 'disabled', 'variant'], template: '<button class="btn"><slot /></button>' },
  Select: { props: ['modelValue', 'options'], emits: ['update:modelValue'], template: '<select class="select"><slot /></select>' },
  Badge: { template: '<span class="badge"><slot /></span>' },
  DataContainer: { props: ['loading', 'hasData', 'emptyText'], template: '<div class="data-container"><slot /></div>' },
  Dialog: { props: ['open', 'title'], template: '<div class="dialog"><slot /></div>' },
}

describe('GroupTasks', () => {
  beforeEach(() => {
    teacherGroupTasksMock.data.value = []
    teacherGroupTasksMock.isPending.value = false
  })

  it('renders without error', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = mount(GroupTasks, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })
    expect(wrapper.find('div').exists()).toBe(true)
    expect(wrapper.text()).toContain('合作项目')
  })

  it('renders clone button when tasks exist', () => {
    teacherGroupTasksMock.data.value = [
      { id: 1, title: '小组项目A', status: 'preparing', class_name: '计算机1班' },
    ]
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const wrapper = mount(GroupTasks, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs,
      },
    })
    expect(wrapper.text()).toContain('小组项目A')
    expect(wrapper.text()).toContain('复制')
  })
})
