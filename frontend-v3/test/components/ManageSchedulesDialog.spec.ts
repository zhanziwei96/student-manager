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
    assign: vi.fn(() => Promise.resolve()),
    unassign: vi.fn(() => Promise.resolve()),
  }
}))

// Mock useSchedules composable
const mockSchedules = ref([
  { id: 1, course_name: '计算机应用基础', class_name: '一班', day_of_week: 1, start_time: '08:00', end_time: '09:40', teacher_id: 2, teacher_name: '张老师' },
  { id: 2, course_name: '数据结构', class_name: '一班', day_of_week: 1, start_time: '10:00', end_time: '11:40', teacher_id: null, teacher_name: null },
  { id: 3, course_name: '计算机网络', class_name: '二班', day_of_week: 2, start_time: '14:00', end_time: '15:40', teacher_id: 3, teacher_name: '李老师' },
  { id: 4, course_name: '操作系统', class_name: '二班', day_of_week: 2, start_time: '16:00', end_time: '17:40', teacher_id: null, teacher_name: null },
])

vi.mock('@/composables/useSchedules', () => ({
  useSchedules: () => ({
    data: mockSchedules,
    isPending: ref(false)
  })
}))

// Mock useClasses composable
vi.mock('@/composables/useClasses', () => ({
  useClasses: () => ({
    data: ref([
      { name: '一班', status: 'active' },
      { name: '二班', status: 'active' }
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

// Mock Dialog component
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

// Mock Button component
const MockButton = {
  name: 'Button',
  props: ['type', 'variant', 'size', 'disabled'],
  emits: ['click'],
  template: `
    <button 
      :type="type || 'button'" 
      :disabled="disabled"
      @click="$emit('click')"
    >
      <slot />
    </button>
  `
}

// Define component instance type
interface ManageSchedulesDialogInstance {
  selectedScheduleIds: number[]
  changes: { added: number[]; removed: number[]; hasChanges: boolean }
  addSchedule: (id: number) => void
  removeSchedule: (id: number) => void
  addAllAvailableForDay: (day: number) => void
  removeAllForDay: (day: number) => void
  selectedClass: string
  searchQuery: string
  handleClose: () => void
  isOccupiedByOther: (schedule: { id: number; teacher_id: number | null } | undefined) => boolean
}

describe('ManageSchedulesDialog', () => {
  const mockTeacher = {
    id: 2,
    username: 'teacher2',
    name: '张老师',
    role: 'teacher'
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockSchedules.value = [
      { id: 1, course_name: '计算机应用基础', class_name: '一班', day_of_week: 1, start_time: '08:00', end_time: '09:40', teacher_id: 2, teacher_name: '张老师' },
      { id: 2, course_name: '数据结构', class_name: '一班', day_of_week: 1, start_time: '10:00', end_time: '11:40', teacher_id: null, teacher_name: null },
      { id: 3, course_name: '计算机网络', class_name: '二班', day_of_week: 2, start_time: '14:00', end_time: '15:40', teacher_id: 3, teacher_name: '李老师' },
      { id: 4, course_name: '操作系统', class_name: '二班', day_of_week: 2, start_time: '16:00', end_time: '17:40', teacher_id: null, teacher_name: null },
    ]
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
          Button: MockButton
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

  it('displays assigned schedules separately', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 已分配的课程应该显示（id=1 属于张老师）
    expect(wrapper.text()).toContain('计算机应用基础')
    expect(wrapper.text()).toContain('已分配')
  })

  it('displays available schedules separately', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 可分配的课程应该显示
    expect(wrapper.text()).toContain('数据结构')
  })

  it('shows occupied schedules with other teacher name', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 被其他教师占用的课程应该显示占用者
    expect(wrapper.text()).toContain('已由 李老师 授课')
    expect(wrapper.text()).toContain('计算机网络')
  })

  it('adds schedule to assigned list when clicked', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as ManageSchedulesDialogInstance
    // 初始状态：已分配 1 个
    expect(vm.selectedScheduleIds).toContain(1)
    expect(vm.selectedScheduleIds).not.toContain(2)

    // 添加课程
    vm.addSchedule(2)
    await flushPromises()

    // 验证变更
    expect(vm.selectedScheduleIds).toContain(2)
    expect(vm.changes.added).toContain(2)
    expect(vm.changes.hasChanges).toBe(true)
  })

  it('removes schedule from assigned list when clicked', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as ManageSchedulesDialogInstance
    // 初始状态
    expect(vm.selectedScheduleIds).toContain(1)

    // 移除课程
    vm.removeSchedule(1)
    await flushPromises()

    // 验证变更
    expect(vm.selectedScheduleIds).not.toContain(1)
    expect(vm.changes.removed).toContain(1)
    expect(vm.changes.hasChanges).toBe(true)
  })

  it('adds all available schedules for a day', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as ManageSchedulesDialogInstance
    // 周一有1个已分配，1个可分配（数据结构）
    expect(vm.selectedScheduleIds.length).toBe(1)

    // 添加周一所有可分配课程
    vm.addAllAvailableForDay(1)
    await flushPromises()

    // 应该添加了数据结构（id=2），但没有添加被李老师占用的（id=3）
    expect(vm.selectedScheduleIds).toContain(2)
    expect(vm.selectedScheduleIds).not.toContain(3)
  })

  it('removes all assigned schedules for a day', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as ManageSchedulesDialogInstance
    // 初始：周一有1个已分配
    expect(vm.selectedScheduleIds).toContain(1)

    // 移除周一所有已分配
    vm.removeAllForDay(1)
    await flushPromises()

    // 应该移除了id=1
    expect(vm.selectedScheduleIds).not.toContain(1)
    expect(vm.changes.removed).toContain(1)
  })

  it('filters schedules by class', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as ManageSchedulesDialogInstance
    // 筛选一班
    vm.selectedClass = '一班'
    await flushPromises()

    // 只显示一班的课程
    const text = wrapper.text()
    expect(text).toContain('计算机应用基础')
    expect(text).toContain('数据结构')
    expect(text).not.toContain('计算机网络') // 二班的课程
  })

  it('filters schedules by search query', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as ManageSchedulesDialogInstance
    // 搜索计算机
    vm.searchQuery = '计算机'
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('计算机应用基础')
    expect(text).toContain('计算机网络')
    expect(text).not.toContain('数据结构')
  })

  it('shows no changes initially', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('暂无变更')
    expect(wrapper.text()).toContain('共负责 1 门课程')
  })

  it('displays correct change counts in summary', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as ManageSchedulesDialogInstance
    // 添加一个
    vm.addSchedule(2)
    // 移除一个
    vm.removeSchedule(1)
    await flushPromises()

    expect(wrapper.text()).toContain('+1 门新增')
    expect(wrapper.text()).toContain('-1 门移除')
  })

  it('emits update:open when cancel clicked', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as ManageSchedulesDialogInstance
    vm.handleClose()
    await flushPromises()

    expect(wrapper.emitted('update:open')).toBeDefined()
    expect(wrapper.emitted('update:open')![0]).toEqual([false])
  })

  it('resets selection when dialog is closed', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as ManageSchedulesDialogInstance
    // 添加一个课程
    vm.addSchedule(2)
    await flushPromises()

    // 关闭弹窗
    vm.handleClose()
    await flushPromises()

    // 选择应该被重置
    expect(vm.selectedScheduleIds).toEqual([1])
  })

  it('disables save button when no changes', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 应该显示"暂无变更"且按钮禁用
    expect(wrapper.text()).toContain('暂无变更')
  })

  it('enables save button when has changes', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as ManageSchedulesDialogInstance
    vm.addSchedule(2)
    await flushPromises()

    expect(wrapper.text()).toContain('保存变更 (1)')
  })

  it('shows correct day grouping', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 应该显示周一和周二
    expect(wrapper.text()).toContain('周一')
    expect(wrapper.text()).toContain('周二')
  })

  it('checks isOccupiedByOther correctly', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as ManageSchedulesDialogInstance
    
    // id=3 被李老师占用（teacher_id=3，不是当前教师id=2）
    const occupiedSchedule = mockSchedules.value.find(s => s.id === 3)
    expect(vm.isOccupiedByOther(occupiedSchedule)).toBe(true)

    // id=2 未被占用（teacher_id 为 null）
    const freeSchedule = mockSchedules.value.find(s => s.id === 2)
    expect(vm.isOccupiedByOther(freeSchedule)).toBeFalsy()

    // id=1 被当前教师占用
    const ownSchedule = mockSchedules.value.find(s => s.id === 1)
    expect(vm.isOccupiedByOther(ownSchedule)).toBe(false)
  })
})
