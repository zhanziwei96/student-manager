/**
 * @vitest-environment jsdom
 *
 * 管理员学生管理页 - 按班级禁用（学期归档，多选班级）功能测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Students from '@/views/admin/Students.vue'

// Toast 间谍（hoisted 以便在断言中引用）
const holder = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn(),
  disableByClass: vi.fn(() => Promise.resolve({ disabled_count: 3, class_names: ['一班'] })),
}))

vi.mock('@/composables', () => ({
  useStudents: () => ({
    data: ref([]),
    isPending: ref(false),
    error: ref(null),
    refetch: vi.fn(),
  }),
  useStudentCreate: () => ({
    mutateAsync: vi.fn(),
    isPending: ref(false),
  }),
  useToast: () => ({
    success: holder.success,
    error: holder.error,
  }),
}))

vi.mock('@/api', () => ({
  studentsApi: {
    disableByClass: holder.disableByClass,
  },
}))

vi.mock('@/features/students', () => ({
  StudentFilters: { template: '<div />' },
  useStudentFilters: () => ({
    filters: ref({ searchQuery: '', className: '' }),
    classOptions: ref([
      { value: '', label: '全部班级', count: 5 },
      { value: '一班', label: '一班 (3人)', count: 3 },
      { value: '二班', label: '二班 (2人)', count: 2 },
    ]),
    filteredStudents: ref([]),
    setSearchQuery: vi.fn(),
    setClassFilter: vi.fn(),
    selectFirstClass: vi.fn(),
  }),
}))

// Mock Dialog 避免 Teleport 问题
const MockDialog = {
  name: 'Dialog',
  props: ['open', 'title', 'description'],
  emits: ['update:open'],
  template: `
    <div v-if="open" class="mock-dialog">
      <h3>{{ title }}</h3>
      <slot />
      <slot name="footer" />
    </div>
  `,
}

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  return mount(Students, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Dialog: MockDialog,
        Card: { template: '<div><slot /></div>' },
        Badge: { template: '<span><slot /></span>' },
        DataContainer: { template: '<div><slot /></div>' },
      },
    },
  })
}

/** 打开按班级禁用弹窗 */
const openDialog = async (wrapper: ReturnType<typeof createWrapper>) => {
  await wrapper.find('[data-testid="disable-by-class-btn"]').trigger('click')
  await flushPromises()
  return wrapper.find('.mock-dialog')
}

describe('Admin Students - 按班级禁用（多选）', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('渲染"按班级禁用"按钮', () => {
    const wrapper = createWrapper()
    const btn = wrapper.find('[data-testid="disable-by-class-btn"]')
    expect(btn.exists()).toBe(true)
    expect(btn.text()).toContain('按班级禁用')
  })

  it('点击按钮打开弹窗并展示班级复选框（不含"全部班级"）', async () => {
    const wrapper = createWrapper()
    const dialog = await openDialog(wrapper)

    expect(dialog.exists()).toBe(true)
    expect(dialog.find('h3').text()).toBe('按班级禁用')

    const checkboxes = dialog.findAll('input[type="checkbox"]')
    expect(checkboxes).toHaveLength(2)
    expect(dialog.text()).toContain('一班 (3人)')
    expect(dialog.text()).toContain('二班 (2人)')
    expect(dialog.text()).not.toContain('全部班级')
  })

  it('未勾选任何班级时确认按钮禁用', async () => {
    const wrapper = createWrapper()
    const dialog = await openDialog(wrapper)

    const confirmBtn = dialog.find('[data-testid="confirm-disable-btn"]')
    expect(confirmBtn.attributes('disabled')).toBeDefined()

    // 勾选后按钮可用
    await dialog.findAll('input[type="checkbox"]')[0].setValue(true)
    expect(dialog.find('[data-testid="confirm-disable-btn"]').attributes('disabled')).toBeUndefined()
  })

  it('勾选单个班级确认后调用 API（参数为数组）并显示成功提示', async () => {
    const wrapper = createWrapper()
    const dialog = await openDialog(wrapper)

    await dialog.findAll('input[type="checkbox"]')[0].setValue(true)
    await dialog.find('[data-testid="confirm-disable-btn"]').trigger('click')
    await flushPromises()

    expect(holder.disableByClass).toHaveBeenCalledWith(['一班'])
    expect(holder.success).toHaveBeenCalledWith('已禁用 3 名学生')
    // 成功后弹窗关闭
    expect(wrapper.find('.mock-dialog').exists()).toBe(false)
  })

  it('勾选多个班级确认后调用 API 传入全部班级', async () => {
    const wrapper = createWrapper()
    const dialog = await openDialog(wrapper)

    const checkboxes = dialog.findAll('input[type="checkbox"]')
    await checkboxes[0].setValue(true)
    await checkboxes[1].setValue(true)

    // 提示文案显示选中班级数量
    expect(dialog.text()).toContain('将禁用 2 个班级的所有学生账号')

    await dialog.find('[data-testid="confirm-disable-btn"]').trigger('click')
    await flushPromises()

    expect(holder.disableByClass).toHaveBeenCalledWith(['一班', '二班'])
  })

  it('取消勾选后从选中列表移除', async () => {
    const wrapper = createWrapper()
    const dialog = await openDialog(wrapper)

    const checkboxes = dialog.findAll('input[type="checkbox"]')
    await checkboxes[0].setValue(true)
    await checkboxes[1].setValue(true)
    await checkboxes[0].setValue(false)

    await dialog.find('[data-testid="confirm-disable-btn"]').trigger('click')
    await flushPromises()

    expect(holder.disableByClass).toHaveBeenCalledWith(['二班'])
  })

  it('API 失败时显示错误提示且不关闭弹窗', async () => {
    holder.disableByClass.mockRejectedValueOnce(new Error('无权限'))
    const wrapper = createWrapper()
    const dialog = await openDialog(wrapper)

    await dialog.findAll('input[type="checkbox"]')[0].setValue(true)
    await dialog.find('[data-testid="confirm-disable-btn"]').trigger('click')
    await flushPromises()

    expect(holder.error).toHaveBeenCalled()
    expect(wrapper.find('.mock-dialog').exists()).toBe(true)
  })
})
