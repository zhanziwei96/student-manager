/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import StudentCheckin from '@/views/student/Checkin.vue'

const mockDoCheckin = vi.fn()
const mockToastSuccess = vi.fn()
const mockToastError = vi.fn()

// 可变 mock 状态：课堂默认带座位图（seat_classroom_id: 7），座位默认两个空位
const courseSessionData = ref<any>({
  id: 10,
  active: true,
  course_name: '计算机基础',
  teacher_name: '李老师',
  start_time: '2026-04-01T10:00:00',
  seat_classroom_id: 7,
})

const twoEmptySeats = () => ({
  classroom: { id: 7, name: '机房302', rows: 1, cols: 2, status: 'active', seat_count: 2 },
  seats: [
    { seat_id: 71, seat_no: 'P11', row: 1, col: 1, is_broken: false, state: 'empty', student_id: null, student_name: null },
    { seat_id: 72, seat_no: 'P12', row: 1, col: 2, is_broken: false, state: 'empty', student_id: null, student_name: null },
  ],
})
const seatMapData = ref<any>(twoEmptySeats())
// 模拟签到成功后 my-checkin-status 重取：hasCheckedIn 立即翻 true（回归 fix/seat-animator-unmount 的竞态）
const hasCheckedInRef = ref(false)
const sessionCheckinRef = ref<any>(null)

vi.mock('@/composables/useStudentProfile', () => ({
  useStudentProfile: () => ({
    data: ref({ student_id: '2024001', name: '张三', class_name: '计算机1班', class_id: 3 }),
    isPending: ref(false),
  }),
}))

vi.mock('@/composables/useStudentCheckin', () => ({
  useStudentCourseSession: () => ({
    data: courseSessionData,
    isPending: ref(false),
    error: ref(null),
    refetch: vi.fn(),
    hasActiveSession: ref(true),
  }),
  useStudentSelfCheckin: () => ({
    mutateAsync: mockDoCheckin,
    isPending: ref(false),
    error: ref(null),
    isSuccess: ref(false),
  }),
  useHasCheckedInSession: () => ({
    hasCheckedIn: hasCheckedInRef,
    sessionCheckin: sessionCheckinRef,
    isPending: ref(false),
  }),
}))

vi.mock('@/composables/useSeatMap', () => ({
  useSeatMap: () => ({
    data: seatMapData,
    isPending: ref(false),
    error: ref(null),
  }),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    success: mockToastSuccess,
    error: mockToastError,
    warning: vi.fn(),
    info: vi.fn(),
  }),
}))

const MockSeatMap = {
  name: 'SeatMap',
  props: ['classroom', 'seats', 'mode', 'selectedSeatId'],
  emits: ['seat-click'],
  template:
    '<div class="mock-seatmap"><button v-for="s in seats" :key="s.seat_id" type="button" class="mock-seat" @click="$emit(\'seat-click\', s)">{{ s.seat_no }}</button></div>',
}

const MockAnimator = {
  name: 'SeatCheckinAnimator',
  props: ['state'],
  emits: ['finished'],
  template: '<div class="mock-animator" :data-state="state" />',
}

function mountPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return mount(StudentCheckin, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Card: { template: '<div class="mock-card"><slot /></div>' },
        Button: { template: '<button class="mock-button"><slot /></button>' },
        Badge: { template: '<span class="mock-badge"><slot /></span>' },
        DataContainer: { template: '<div><slot /></div>' },
        Input: {
          props: ['modelValue', 'placeholder', 'maxlength'],
          emits: ['update:modelValue'],
          template:
            '<input class="mock-input" :value="modelValue" :maxlength="maxlength" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        SeatMap: MockSeatMap,
        SeatCheckinAnimator: MockAnimator,
      },
    },
  })
}

const findConfirmButton = (wrapper: ReturnType<typeof mountPage>) =>
  wrapper.findAll('button').find((b) => b.text().includes('确认签到'))

describe('学生座位签到', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockDoCheckin.mockReset()
    hasCheckedInRef.value = false
    sessionCheckinRef.value = null
    courseSessionData.value = {
      id: 10,
      active: true,
      course_name: '计算机基础',
      teacher_name: '李老师',
      start_time: '2026-04-01T10:00:00',
      seat_classroom_id: 7,
    }
    seatMapData.value = twoEmptySeats()
  })

  it('有座位图时渲染 SeatMap', async () => {
    const wrapper = mountPage()
    await flushPromises()
    expect(wrapper.find('.mock-seatmap').exists()).toBe(true)
  })

  it('无座位图时保持原验证码卡片，不渲染 SeatMap', async () => {
    courseSessionData.value = { ...courseSessionData.value, seat_classroom_id: null }
    const wrapper = mountPage()
    await flushPromises()
    expect(wrapper.find('.mock-seatmap').exists()).toBe(false)
    expect(wrapper.text()).toContain('输入验证码签到')
  })

  it('点座位 + 输验证码 → 提交带 seat_id', async () => {
    mockDoCheckin.mockResolvedValue({ id: 1 })
    const wrapper = mountPage()
    await flushPromises()

    await wrapper.findAll('.mock-seat')[0].trigger('click')
    await wrapper.find('.mock-input').setValue('123456')
    await findConfirmButton(wrapper)!.trigger('click')
    await flushPromises()

    expect(mockDoCheckin).toHaveBeenCalledWith(
      expect.objectContaining({ verification_code: '123456', seat_id: 71 }),
    )
  })

  it('未选座位时提交被拦截', async () => {
    const wrapper = mountPage()
    await flushPromises()

    await wrapper.find('.mock-input').setValue('123456')
    await findConfirmButton(wrapper)!.trigger('click')
    await flushPromises()

    expect(mockDoCheckin).not.toHaveBeenCalled()
    expect(mockToastError).toHaveBeenCalledWith('请先选择座位')
  })

  it('签到成功 → animator success → finished 后才弹成功提示', async () => {
    mockDoCheckin.mockResolvedValue({ id: 1 })
    const wrapper = mountPage()
    await flushPromises()

    await wrapper.findAll('.mock-seat')[0].trigger('click')
    await wrapper.find('.mock-input').setValue('123456')
    await findConfirmButton(wrapper)!.trigger('click')
    await flushPromises()

    const animator = wrapper.findComponent({ name: 'SeatCheckinAnimator' })
    expect(animator.props('state')).toBe('success')
    // 动画播完前不弹 toast
    expect(mockToastSuccess).not.toHaveBeenCalled()

    animator.vm.$emit('finished')
    await flushPromises()
    expect(mockToastSuccess).toHaveBeenCalledWith('签到成功！')
  })

  it('回归：hasCheckedIn 翻 true 后动画器不被卸载，已签到卡片等动画播完才出现', async () => {
    // 模拟真实竞态：doCheckin 成功后 my-checkin-status 立即重取，hasCheckedIn 翻 true
    mockDoCheckin.mockImplementation(async () => {
      hasCheckedInRef.value = true
      sessionCheckinRef.value = { checkin_time: '2026-04-01T10:05:00' }
      return {}
    })
    const wrapper = mountPage()
    await flushPromises()

    await wrapper.findAll('.mock-seat')[0].trigger('click')
    await wrapper.find('.mock-input').setValue('123456')
    await findConfirmButton(wrapper)!.trigger('click')
    await flushPromises()

    // hasCheckedIn 已为 true，但动画器仍在 DOM 中且状态为 success
    const animator = wrapper.findComponent({ name: 'SeatCheckinAnimator' })
    expect(animator.exists()).toBe(true)
    expect(animator.props('state')).toBe('success')
    // 已签到卡片在动画播完前不出现
    expect(wrapper.text()).not.toContain('本节课已完成签到')

    animator.vm.$emit('finished')
    await flushPromises()
    // 播完后卡片出现 + toast
    expect(wrapper.text()).toContain('本节课已完成签到')
    expect(mockToastSuccess).toHaveBeenCalledWith('签到成功！')
  })

  it('签到失败 → animator fail → finished 后清验证码、保留座位、toast 后端 message', async () => {
    mockDoCheckin.mockRejectedValue(new Error('座位已被占用'))
    const wrapper = mountPage()
    await flushPromises()

    await wrapper.findAll('.mock-seat')[0].trigger('click')
    await wrapper.find('.mock-input').setValue('123456')
    await findConfirmButton(wrapper)!.trigger('click')
    await flushPromises()

    const animator = wrapper.findComponent({ name: 'SeatCheckinAnimator' })
    expect(animator.props('state')).toBe('fail')
    expect(mockToastError).not.toHaveBeenCalled()

    animator.vm.$emit('finished')
    await flushPromises()
    expect(mockToastError).toHaveBeenCalledWith('座位已被占用')
    // 验证码已清空
    expect((wrapper.find('.mock-input').element as HTMLInputElement).value).toBe('')

    // 座位保留：再输验证码直接提交仍带原 seat_id
    await wrapper.find('.mock-input').setValue('654321')
    await findConfirmButton(wrapper)!.trigger('click')
    await flushPromises()
    expect(mockDoCheckin).toHaveBeenCalledTimes(2)
    expect(mockDoCheckin).toHaveBeenLastCalledWith(
      expect.objectContaining({ verification_code: '654321', seat_id: 71 }),
    )
  })

  it('我的固定座位故障时显示换座提示', async () => {
    seatMapData.value = {
      classroom: { id: 7, name: '机房302', rows: 1, cols: 2, status: 'active', seat_count: 2 },
      seats: [
        { seat_id: 73, seat_no: 'P13', row: 1, col: 1, is_broken: true, state: 'mine', student_id: '2024001', student_name: '张三' },
        { seat_id: 71, seat_no: 'P11', row: 1, col: 2, is_broken: false, state: 'empty', student_id: null, student_name: null },
      ],
    }
    const wrapper = mountPage()
    await flushPromises()
    expect(wrapper.text()).toContain('你的座位电脑故障，请挑一个空位')
  })
})
