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

vi.mock('@/composables/useStudentCheckin', () => ({
  useStudentClassSession: () => ({
    data: ref({
      active: true,
      course_name: '高等数学',
      teacher_name: '李老师',
      start_time: '2026-04-01T10:00:00',
      location_name: '机房312',
      checkin_radius: 100
    }),
    isPending: ref(false),
    hasActiveSession: ref(true)
  }),
  useStudentSelfCheckin: () => ({
    mutateAsync: vi.fn(),
    isPending: ref(false),
    error: ref(null),
    isSuccess: ref(false),
    locationError: ref(null)
  }),
  useHasCheckedInSession: () => ({
    hasCheckedIn: ref(false),
    sessionCheckin: ref(null),
    isPending: ref(false)
  }),
  useGeolocation: () => ({
    isLocating: ref(false),
    locationError: ref(null),
    position: ref(null),
    getCurrentPosition: vi.fn().mockResolvedValue({ lat: 39.90923, lng: 116.397428 })
  })
}))

vi.mock('@/composables/useCheckins', () => ({
  useTodayCheckins: () => ({
    data: ref([])
  })
}))

// Mock device fingerprint
vi.mock('@/lib/device', () => ({
  getDeviceFingerprint: vi.fn().mockResolvedValue('device123'),
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

describe('Student Checkin with GPS', () => {
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
    return mount(StudentCheckin, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs: {
          Card: MockCard,
          Button: MockButton,
          Badge: MockBadge,
          Toast: { template: '<div class="mock-toast" />' }
        }
      }
    })
  }

  it('displays location info when active session has location', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 验证显示签到位置信息
    expect(wrapper.text()).toContain('签到地点')
    expect(wrapper.text()).toContain('机房312')
    expect(wrapper.text()).toContain('100米')
  })

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
