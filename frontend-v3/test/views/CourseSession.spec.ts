/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import CourseSession from '@/views/teacher/CourseSession.vue'

// Mock stores
vi.mock('@/stores', () => ({
  useAuthStore: () => ({
    user: { id: 1, name: '张老师', role: 'teacher' }
  })
}))

// Mock composables
vi.mock('@/composables', () => ({
  useCourseSessions: () => ({
    data: ref([]),
    error: ref(null),
    refetch: vi.fn()
  }),
  useCourseSessionStart: () => ({
    mutateAsync: vi.fn(),
    isPending: ref(false)
  }),
  useCourseSessionEnd: () => ({
    mutateAsync: vi.fn(),
    isPending: ref(false)
  }),
  useStudentCheckIn: () => ({
    mutateAsync: vi.fn(),
    isPending: ref(false)
  }),
  useActiveClassSessions: () => ({
    data: ref([])
  }),
  useTodaySchedules: () => ({
    data: ref([]),
    isPending: ref(false),
    error: ref(null),
    refetch: vi.fn()
  }),
  useToast: () => ({
    show: ref(false),
    message: ref(''),
    variant: ref('default'),
    success: vi.fn(),
    error: vi.fn(),
    showErrorToast: vi.fn(),
    showSuccessToast: vi.fn()
  }),
  useNetworkError: () => ({
    networkError: ref(null),
    setError: vi.fn(),
    clearError: vi.fn()
  })
}))

vi.mock('@/composables/useClasses', () => ({
  useClasses: () => ({
    data: ref([
      { name: '计算机1班', status: 'active' },
      { name: '软件工程班', status: 'active' }
    ])
  }),
  useClassStudents: () => ({
    data: ref([]),
    isPending: ref(false)
  })
}))

vi.mock('@/composables/useCheckins', () => ({
  useSessionCheckins: () => ({
    data: ref([]),
    refetch: vi.fn()
  }),
  useSessionCheckinStats: () => ({
    data: ref(null),
    refetch: vi.fn()
  })
}))

// Mock components
const MockCard = {
  template: '<div class="mock-card"><slot /></div>'
}

const MockButton = {
  props: ['loading', 'disabled', 'variant'],
  template: '<button class="mock-button" :disabled="disabled"><slot /></button>'
}

const MockSelect = {
  props: ['modelValue', 'placeholder', 'options'],
  emits: ['update:modelValue'],
  template: `
    <select
      class="mock-select"
      :value="modelValue"
      @change="$emit('update:modelValue', $event.target.value)"
    >
      <option value="">{{ placeholder }}</option>
      <option v-for="opt in options" :key="opt.value" :value="opt.value">
        {{ opt.label }}
      </option>
    </select>
  `
}

const MockInput = {
  props: ['modelValue', 'type', 'step', 'placeholder'],
  emits: ['update:modelValue'],
  template: '<input :value="modelValue" :type="type" :step="step" :placeholder="placeholder" @input="$emit(\'update:modelValue\', $event.target.value)" /><span class="mock-input-placeholder">{{ placeholder }}</span>'
}

const MockDialog = {
  props: ['open', 'title'],
  emits: ['update:open'],
  template: '<div v-if="open" class="mock-dialog"><h3>{{ title }}</h3><slot /></div>'
}

const MockNetworkErrorBanner = {
  props: ['message'],
  emits: ['retry', 'dismiss'],
  template: '<div v-if="message" class="mock-error-banner">{{ message }}</div>'
}

const MockCheckinStats = {
  props: ['stats'],
  template: '<div class="mock-checkin-stats"><slot /></div>'
}

const MockStudentCheckinGrid = {
  props: ['students', 'loading', 'searchQuery'],
  emits: ['update:searchQuery', 'quickCheckIn'],
  template: '<div class="mock-student-grid"><slot /></div>'
}

describe('CourseSession', () => {
  const createTestQueryClient = () => new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 }
    }
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mountComponent = () => {
    const queryClient = createTestQueryClient()
    return mount(CourseSession, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs: {
          Card: MockCard,
          Button: MockButton,
          Select: MockSelect,
          Input: MockInput,
          Badge: { template: '<span class="mock-badge"><slot /></span>' },
          Dialog: MockDialog,
          Toast: { template: '<div class="mock-toast" />' },
          NetworkErrorBanner: MockNetworkErrorBanner,
          CheckinStats: MockCheckinStats,
          StudentCheckinGrid: MockStudentCheckinGrid
        }
      }
    })
  }

  it('displays course selection input and class select', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const selects = wrapper.findAll('.mock-select')
    expect(selects.length).toBeGreaterThanOrEqual(1)
    expect(wrapper.text()).toContain('选择课程（可选）')
  })

  it('displays available classes', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('计算机1班')
    expect(wrapper.text()).toContain('软件工程班')
  })

  it('allows entering course name and selecting class', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const inputs = wrapper.findAll('input')
    const selects = wrapper.findAll('.mock-select')

    // Enter course name
    if (inputs.length > 0) {
      await inputs[0].setValue('高等数学')
      await flushPromises()
      expect(inputs[0].element.value).toBe('高等数学')
    }

    // Select class (selects[0] is course selector, selects[1] is class selector)
    if (selects.length > 1) {
      await selects[1].setValue('计算机1班')
      await flushPromises()
      expect(selects[1].element.value).toBe('计算机1班')
    }
  })

  it('displays start button with correct text', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('开始上课')
  })

  it('shows start session form when no active session', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('开始新课堂')
    expect(wrapper.text()).toContain('选择班级开始上课')
  })

  it('displays class selection placeholder', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('选择班级')
  })
})
