/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import ManageSchedulesDialog from '@/components/admin/ManageSchedulesDialog.vue'

// Create a test query client
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      gcTime: 0,
      staleTime: 0,
    },
  },
})

// Mock the API
vi.mock('@/api/schedules', () => ({
  schedulesApi: {
    assignTeacher: vi.fn(() => Promise.resolve()),
    unassignTeacher: vi.fn(() => Promise.resolve()),
    getByTeacher: vi.fn(() => Promise.resolve([]))
  }
}))

// Mock useSchedules composable
vi.mock('@/composables/useSchedules', () => ({
  useSchedules: () => ({
    data: ref([
      { id: 1, course_name: '数学', teacher_id: 1, teacher_name: '张老师', day_of_week: 1, start_time: '08:00', end_time: '09:00', class_name: '一年级一班' },
      { id: 2, course_name: '语文', teacher_id: null, teacher_name: null, day_of_week: 1, start_time: '09:00', end_time: '10:00', class_name: '一年级一班' },
      { id: 3, course_name: '英语', teacher_id: 2, teacher_name: '李老师', day_of_week: 2, start_time: '10:00', end_time: '11:00', class_name: '二年级一班' }
    ]),
    isPending: ref(false),
    refetch: vi.fn()
  })
}))

// Mock useClasses composable
vi.mock('@/composables/useClasses', () => ({
  useClasses: () => ({
    data: ref([
      { name: '一年级一班' },
      { name: '二年级一班' }
    ]),
    isPending: ref(false)
  })
}))

// Mock useToast
vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    showToast: vi.fn()
  })
}))

// Mock Dialog component to avoid Teleport issues
const MockDialog = {
  name: 'Dialog',
  props: ['open', 'title'],
  emits: ['update:open'],
  template: `
    <div v-if="open" class="mock-dialog">
      <h3>{{ title }}</h3>
      <slot />
      <slot name="footer" />
    </div>
  `
}

describe('ManageSchedulesDialog', () => {
  const mockTeacher = {
    id: 1,
    username: 'teacher1',
    name: '张老师',
    role: 'teacher',
    assigned_classes: []
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mountComponent = (props = {}) => {
    const queryClient = createTestQueryClient()
    return mount(ManageSchedulesDialog, {
      props: {
        teacher: mockTeacher,
        open: true,
        ...props
      },
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs: {
          Dialog: MockDialog,
          Button: { template: '<button><slot /></button>' },
          Checkbox: { 
            props: ['checked'],
            template: '<input type="checkbox" :checked="checked" />'
          }
        }
      }
    })
  }

  it('renders correctly when open', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.find('.mock-dialog').exists()).toBe(true)
    expect(wrapper.text()).toContain('管理课表')
    expect(wrapper.text()).toContain('张老师')
  })

  it('displays schedules grouped by day', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('周一')
    expect(wrapper.text()).toContain('数学')
    expect(wrapper.text()).toContain('语文')
  })

  it('shows selected count correctly', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // Teacher with id=1 has one course assigned
    expect(wrapper.text()).toContain('已选择: 1 门课程')
  })

  it('emits update:open when cancel clicked', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // Find cancel button and click it
    const buttons = wrapper.findAll('button')
    const cancelButton = buttons.find(b => b.text().includes('取消'))
    
    if (cancelButton) {
      await cancelButton.trigger('click')
      expect(wrapper.emitted('update:open')).toBeDefined()
      expect(wrapper.emitted('update:open')![0]).toEqual([false])
    }
  })

  it('shows warning when course is assigned to other teacher', async () => {
    const otherTeacher = {
      id: 2,
      username: 'teacher2',
      name: '李老师',
      role: 'teacher',
      assigned_classes: []
    }

    const wrapper = mountComponent({ teacher: otherTeacher })
    await flushPromises()

    // Should show warning that course is already assigned to another teacher
    const text = wrapper.text()
    expect(text).toContain('已由')
    expect(text).toContain('授课')
  })
})
