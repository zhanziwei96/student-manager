/**
 * @vitest-environment jsdom
 *
 * 手动开课表单：教室下拉（可选）→ startSession 载荷带 classroom。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import CourseSession from '@/views/teacher/CourseSession.vue'

const startSession = vi.fn()

vi.mock('@/stores', () => ({
  useAuthStore: () => ({
    user: { id: 1, name: '张老师', role: 'teacher' },
  }),
}))

vi.mock('@/composables', () => ({
  useCourseSessions: () => ({
    data: ref([]),
    error: ref(null),
    refetch: vi.fn(),
  }),
  useCourseSessionStart: () => ({
    mutateAsync: startSession,
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
    data: ref([]),
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
    data: ref(null),
    isPending: ref(false),
    error: ref(null),
  }),
}))

vi.mock('@/api/seats', () => ({
  classroomsApi: {
    list: vi.fn().mockResolvedValue([
      { id: 1, name: '机房302', rows: 3, cols: 4, status: 'active', seat_count: 12 },
      { id: 2, name: '旧机房', rows: 2, cols: 2, status: 'archived', seat_count: 4 },
    ]),
    getSeats: vi.fn(),
  },
  seatsApi: { setBroken: vi.fn() },
  seatOverridesApi: { set: vi.fn(), clear: vi.fn() },
}))

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

const mountComponent = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: 0 } },
  })
  return mount(CourseSession, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Card: { template: '<div class="mock-card"><slot /></div>' },
        Button: {
          props: ['loading', 'disabled', 'variant', 'size'],
          template: '<button class="mock-button" :disabled="disabled"><slot /></button>',
        },
        Select: MockSelect,
        Input: {
          props: ['modelValue', 'type', 'placeholder'],
          emits: ['update:modelValue'],
          template: '<input :value="modelValue" :type="type" :placeholder="placeholder" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        Badge: { template: '<span class="mock-badge"><slot /></span>' },
        ResponsiveDialog: {
          props: ['open', 'title'],
          template: '<div v-if="open" class="mock-dialog"><slot name="description" /><slot /><slot name="footer" /></div>',
        },
        NetworkErrorBanner: { template: '<div />' },
        CheckinStats: { template: '<div />' },
        StudentCheckinGrid: { template: '<div />' },
        QRCodeDisplay: { template: '<div />' },
        SeatMap: { template: '<div />' },
      },
    },
  })
}

describe('手动开课表单：教室下拉', () => {
  beforeEach(() => {
    startSession.mockReset()
    startSession.mockResolvedValue({})
  })

  it('渲染教室下拉，只列 active 教室', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const classroomSelect = wrapper
      .findAll('.mock-select')
      .find(s => s.html().includes('选择教室'))
    expect(classroomSelect).toBeTruthy()
    expect(classroomSelect!.text()).toContain('机房302（3×4）')
    expect(classroomSelect!.text()).not.toContain('旧机房')
  })

  it('选择班级 + 教室后开课，载荷带 classroom', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const selects = wrapper.findAll('.mock-select')
    const classSelect = selects.find(s => s.html().includes('请选择班级'))!
    const classroomSelect = selects.find(s => s.html().includes('选择教室'))!

    await classSelect.setValue(3)
    await classroomSelect.setValue('机房302')

    await wrapper.findAll('.mock-button')
      .find(b => b.text().includes('开始上课'))!
      .trigger('click')
    await flushPromises()

    expect(startSession).toHaveBeenCalledWith(
      // mock select 的 change 事件产出字符串值（真实 Select 组件保留 number 类型）
      expect.objectContaining({ classId: '3', classroom: '机房302' }),
    )
  })

  it('不选教室开课，classroom 为 undefined（走原纯验证码流程）', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const classSelect = wrapper.findAll('.mock-select')
      .find(s => s.html().includes('请选择班级'))!
    await classSelect.setValue(3)

    await wrapper.findAll('.mock-button')
      .find(b => b.text().includes('开始上课'))!
      .trigger('click')
    await flushPromises()

    expect(startSession).toHaveBeenCalledWith(
      expect.objectContaining({ classId: '3', classroom: undefined }),
    )
  })
})
