/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import CourseSession from '@/views/teacher/CourseSession.vue'

// 可变 mock 状态：默认活跃课堂带座位图（seat_classroom_id: 7）
const activeSession = () => ({
  id: 10,
  session_code: 'ABC123',
  course_name: '计算机基础',
  class_name: '2026届计算机1班',
  teacher_id: 1,
  teacher_name: '张老师',
  start_time: '2026-04-01T10:00:00',
  status: 'active',
  source_type: 'manual',
  seat_classroom_id: 7,
})
const sessionsData = ref<any[]>([activeSession()])

const seatMapData = ref<any>({
  classroom: { id: 7, name: '机房302', rows: 1, cols: 2, status: 'active', seat_count: 2 },
  seats: [
    { seat_id: 71, seat_no: 'P11', row: 1, col: 1, is_broken: false, state: 'empty', student_id: null, student_name: null },
    { seat_id: 72, seat_no: 'P12', row: 1, col: 2, is_broken: false, state: 'empty', student_id: null, student_name: null },
  ],
})

vi.mock('@/stores', () => ({
  useAuthStore: () => ({
    user: { id: 1, name: '张老师', role: 'teacher' },
  }),
}))

vi.mock('@/composables', () => ({
  useCourseSessions: () => ({
    data: sessionsData,
    error: ref(null),
    refetch: vi.fn(),
  }),
  useCourseSessionStart: () => ({
    mutateAsync: vi.fn(),
    isPending: ref(false),
  }),
  useCourseSessionEnd: () => ({
    mutateAsync: vi.fn(),
    isPending: ref(false),
  }),
  useStudentCheckIn: () => ({
    mutateAsync: vi.fn(),
    isPending: ref(false),
  }),
  useActiveClassSessions: () => ({
    data: ref([]),
  }),
  useTodaySchedules: () => ({
    data: ref([]),
    isPending: ref(false),
    error: ref(null),
    refetch: vi.fn(),
  }),
  useToast: () => ({
    show: ref(false),
    message: ref(''),
    variant: ref('default'),
    success: vi.fn(),
    error: vi.fn(),
  }),
  useNetworkError: () => ({
    networkError: ref(null),
    setError: vi.fn(),
    clearError: vi.fn(),
  }),
}))

vi.mock('@/composables/useClasses', () => ({
  useClasses: () => ({
    data: ref([
      { id: 3, name: '1班', major: '计算机', cohort_year: '2026', display_name: '2026届计算机1班', student_count: 1, status: 'active' },
    ]),
  }),
  useClassStudents: () => ({
    data: ref([{ student_id: 'S001', name: '张三' }]),
    isPending: ref(false),
  }),
}))

vi.mock('@/composables/useCheckins', () => ({
  useSessionCheckins: () => ({
    data: ref([]),
    refetch: vi.fn(),
  }),
}))

vi.mock('@/composables/useTeacherCourses', () => ({
  useTeacherCourses: () => ({
    data: ref([]),
  }),
}))

vi.mock('@/composables/useSeatMap', () => ({
  useSeatMap: () => ({
    data: seatMapData,
    isPending: ref(false),
    error: ref(null),
  }),
}))

vi.mock('@/api/seats', () => ({
  classroomsApi: { list: vi.fn(), getSeats: vi.fn() },
  seatsApi: { setBroken: vi.fn() },
  seatOverridesApi: { set: vi.fn(), clear: vi.fn() },
}))

import { seatsApi, seatOverridesApi } from '@/api/seats'
const mockedSetBroken = vi.mocked(seatsApi.setBroken)
const mockedSetOverride = vi.mocked(seatOverridesApi.set)

const MockSeatMap = {
  name: 'SeatMap',
  props: ['classroom', 'seats', 'mode', 'selectedSeatId'],
  emits: ['seat-click'],
  template:
    '<div class="mock-seatmap"><button v-for="s in seats" :key="s.seat_id" type="button" class="mock-seat" @click="$emit(\'seat-click\', s)">{{ s.seat_no }}</button></div>',
}

const MockCard = { template: '<div class="mock-card"><slot /></div>' }

const MockButton = {
  props: ['loading', 'disabled', 'variant', 'size'],
  template: '<button class="mock-button" :disabled="disabled"><slot /></button>',
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
  `,
}

const MockInput = {
  props: ['modelValue', 'type', 'placeholder'],
  emits: ['update:modelValue'],
  template: '<input :value="modelValue" :type="type" :placeholder="placeholder" @input="$emit(\'update:modelValue\', $event.target.value)" />',
}

const MockResponsiveDialog = {
  props: ['open', 'title'],
  emits: ['update:open'],
  template:
    '<div v-if="open" class="mock-dialog"><h3>{{ title }}</h3><slot name="description" /><slot /><slot name="footer" /></div>',
}

const MockNetworkErrorBanner = {
  props: ['message'],
  emits: ['retry', 'dismiss'],
  template: '<div v-if="message" class="mock-error-banner">{{ message }}</div>',
}

const mountComponent = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: 0 } },
  })
  return mount(CourseSession, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Card: MockCard,
        Button: MockButton,
        Select: MockSelect,
        Input: MockInput,
        Badge: { template: '<span class="mock-badge"><slot /></span>' },
        ResponsiveDialog: MockResponsiveDialog,
        NetworkErrorBanner: MockNetworkErrorBanner,
        CheckinStats: { template: '<div class="mock-checkin-stats" />' },
        StudentCheckinGrid: { template: '<div class="mock-student-grid" />' },
        QRCodeDisplay: { template: '<div class="mock-qrcode" />' },
        SeatMap: MockSeatMap,
      },
    },
  })
}

describe('教师课堂实时座位图', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionsData.value = [activeSession()]
    seatMapData.value = {
      classroom: { id: 7, name: '机房302', rows: 1, cols: 2, status: 'active', seat_count: 2 },
      seats: [
        { seat_id: 71, seat_no: 'P11', row: 1, col: 1, is_broken: false, state: 'empty', student_id: null, student_name: null },
        { seat_id: 72, seat_no: 'P12', row: 1, col: 2, is_broken: false, state: 'empty', student_id: null, student_name: null },
      ],
    }
  })

  it('活跃课堂带 seat_classroom_id 时渲染 SeatMap', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.find('.mock-seatmap').exists()).toBe(true)
  })

  it('课堂无 seat_classroom_id 时不渲染 SeatMap（原页面不变）', async () => {
    sessionsData.value = [{ ...activeSession(), seat_classroom_id: null }]
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.find('.mock-seatmap').exists()).toBe(false)
    expect(wrapper.text()).toContain('学生签到')
  })

  it('教师点座位 → 标记电脑故障 → seatsApi.setBroken(seatId, true)', async () => {
    mockedSetBroken.mockResolvedValue({ id: 71, is_broken: true })
    const wrapper = mountComponent()
    await flushPromises()

    await wrapper.findAll('.mock-seat')[0].trigger('click')
    await flushPromises()

    expect(wrapper.find('.mock-dialog').exists()).toBe(true)
    const brokenButton = wrapper
      .findAll('.mock-dialog button')
      .find((b) => b.text().includes('标记电脑故障'))
    expect(brokenButton).toBeTruthy()
    await brokenButton!.trigger('click')
    await flushPromises()

    expect(mockedSetBroken).toHaveBeenCalledWith(71, true)
  })

  it('教师点座位 → 选学生调座 → seatOverridesApi.set(sessionId, studentId, seatId)', async () => {
    mockedSetOverride.mockResolvedValue({ session_id: 10, student_id: 'S001', seat_id: 71 })
    const wrapper = mountComponent()
    await flushPromises()

    await wrapper.findAll('.mock-seat')[0].trigger('click')
    await flushPromises()

    const select = wrapper.find('.mock-dialog .mock-select')
    expect(select.exists()).toBe(true)
    await select.setValue('S001')
    await flushPromises()

    const overrideButton = wrapper
      .findAll('.mock-dialog button')
      .find((b) => b.text().includes('确认调座'))
    expect(overrideButton).toBeTruthy()
    await overrideButton!.trigger('click')
    await flushPromises()

    expect(mockedSetOverride).toHaveBeenCalledWith(10, 'S001', 71)
  })
})
