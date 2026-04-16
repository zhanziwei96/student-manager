/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import StudentCheckin from '@/views/student/Checkin.vue'

// Mock stores
vi.mock('@/stores', () => ({
  useAuthStore: () => ({
    user: { id: 1, name: '张三', role: 'student' }
  })
}))

// Mock composables
vi.mock('@/composables/useStudentProfile', () => ({
  useStudentProfile: () => ({
    data: ref({
      student_id: '2024001',
      name: '张三',
      class_name: '计算机1班'
    }),
    isPending: ref(false)
  })
}))

const mockRefetchSession = vi.fn()

// 可变 mock 状态，用于在测试中动态切换返回值
const mockCourseSessionState = {
  data: ref({
    active: true,
    course_name: '高等数学',
    teacher_name: '李老师',
    start_time: '2026-04-01T10:00:00'
  }),
  isPending: ref(false),
  error: ref(null),
  refetch: mockRefetchSession,
  hasActiveSession: ref(true)
}

vi.mock('@/composables/useStudentCheckin', () => ({
  useStudentCourseSession: () => mockCourseSessionState,
  useStudentSelfCheckin: () => ({
    mutateAsync: vi.fn(),
    isPending: ref(false),
    error: ref(null),
    isSuccess: ref(false)
  }),
  useHasCheckedInSession: () => ({
    hasCheckedIn: ref(false),
    sessionCheckin: ref(null),
    isPending: ref(false)
  })
}))

vi.mock('@/composables/useCheckins', () => ({
  useSessionCheckins: () => ({
    data: ref([])
  }),
  useSessionCheckinStats: () => ({
    data: ref(null),
    refetch: vi.fn()
  })
}))

// Mock Toast
vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
    showToast: vi.fn(),
    hideToast: vi.fn(),
    clearAll: vi.fn(),
    toasts: ref([])
  })
}))

// Mock device fingerprint
vi.mock('@/lib/device', () => ({
  getEnhancedDeviceFingerprint: vi.fn().mockResolvedValue('device123'),
  getDeviceInfo: vi.fn().mockReturnValue({ userAgent: 'test' })
}))

// Mock components
const MockCard = {
  template: '<div class="mock-card"><slot /></div>'
}

const MockButton = {
  props: ['loading', 'disabled'],
  template: '<button class="mock-button" :disabled="disabled"><slot /></button>'
}

const MockBadge = {
  template: '<span class="mock-badge"><slot /></span>'
}

const MockDataContainer = {
  props: ['loading', 'error', 'hasData', 'emptyText'],
  template: `
    <div v-if="error" class="mock-data-container-error">
      <span class="error-message">{{ error.message }}</span>
      <button class="retry-button" @click="$emit('retry')">重试</button>
    </div>
    <div v-else-if="loading" class="mock-data-container-loading">Loading...</div>
    <div v-else-if="!hasData" class="mock-data-container-empty">{{ emptyText }}</div>
    <slot v-else />
  `
}

describe('Student Checkin with GPS', () => {
  const createTestQueryClient = () => new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 }
    }
  })

  beforeEach(() => {
    vi.clearAllMocks()
    // 重置为默认成功状态
    mockCourseSessionState.data.value = {
      active: true,
      course_name: '高等数学',
      teacher_name: '李老师',
      start_time: '2026-04-01T10:00:00'
    }
    mockCourseSessionState.isPending.value = false
    mockCourseSessionState.error.value = null
    mockCourseSessionState.hasActiveSession.value = true
  })

  const mountComponent = () => {
    const queryClient = createTestQueryClient()
    return mount(StudentCheckin, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs: {
          Card: MockCard,
          Button: MockButton,
          Badge: MockBadge,
          DataContainer: MockDataContainer,
          Toast: { template: '<div class="mock-toast" />' }
        }
      }
    })
  }

  it('shows checkin button when session is active and not checked in', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 验证显示立即签到按钮
    expect(wrapper.text()).toContain('立即签到')
  })

  it('displays student info correctly', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 验证学生信息显示
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('2024001')
    expect(wrapper.text()).toContain('计算机1班')
  })

  it('shows active session status', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 验证显示课堂进行中状态
    expect(wrapper.text()).toContain('课堂进行中')
    expect(wrapper.text()).toContain('李老师')
  })

  it('displays checkin instructions', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 验证签到说明
    expect(wrapper.text()).toContain('签到说明')
    expect(wrapper.text()).toContain('请在老师开启课堂后进行签到')
    expect(wrapper.text()).toContain('每节课只能签到一次')
  })
})

describe('Student Checkin Error Handling (P1-2)', () => {
  const createTestQueryClient = () => new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 }
    }
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mountComponent = (overrides?: Record<string, any>) => {
    const queryClient = createTestQueryClient()
    return mount(StudentCheckin, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs: {
          Card: MockCard,
          Button: MockButton,
          Badge: MockBadge,
          DataContainer: MockDataContainer,
          Toast: { template: '<div class="mock-toast" />' }
        },
        provide: {
          ...overrides
        }
      }
    })
  }

  it('当课堂信息加载失败时应显示错误和重试按钮', async () => {
    mockCourseSessionState.data.value = null
    mockCourseSessionState.error.value = new Error('Network Error: Failed to fetch')
    mockCourseSessionState.hasActiveSession.value = false

    const wrapper = mountComponent()
    await flushPromises()

    // 由于 studentProfile 存在，错误应显示在状态卡片内
    expect(wrapper.text()).toContain('加载课堂信息失败')
    expect(wrapper.text()).toContain('网络连接异常')
    expect(wrapper.text()).toContain('重试')
  })

  it('点击重试按钮应调用 refetchSession', async () => {
    mockCourseSessionState.data.value = null
    mockCourseSessionState.error.value = new Error('Network Error: Failed to fetch')
    mockCourseSessionState.hasActiveSession.value = false

    const wrapper = mountComponent()
    await flushPromises()

    const retryButton = wrapper.find('button')
    expect(retryButton.text()).toContain('重试')
    await retryButton.trigger('click')

    expect(mockRefetchSession).toHaveBeenCalled()
  })
})
