/**
 * @vitest-environment jsdom
 *
 * 管理员学生管理页 - 批量禁用毕业生账号（多选班级）功能测试
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
  disableByClass: vi.fn(() => Promise.resolve({ disabled_count: 3, class_ids: [1] })),
  paginated: null as unknown as Record<string, unknown>,
}))

vi.mock('@/composables', () => ({
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
  usePaginatedStudents: () => holder.paginated,
}))

/** 构造 usePaginatedStudents 的 mock 返回值（各用例可覆盖字段） */
const makePaginated = (overrides: Record<string, unknown> = {}) => ({
  page: ref(1),
  pageSize: 50,
  searchQuery: ref(''),
  classId: ref(''),
  isSearching: ref(false),
  classOptions: ref([
    { value: '', label: '全部班级', count: 0 },
    { value: '1', label: '2026届软件工程1班', count: 0 },
    { value: '2', label: '2026届软件工程2班', count: 0 },
  ]),
  filteredStudents: ref([]),
  total: ref(0),
  totalPages: ref(1),
  isPending: ref(false),
  error: ref(null),
  refetch: vi.fn(),
  setSearchQuery: vi.fn(),
  setClassFilter: vi.fn(),
  selectFirstClass: vi.fn(),
  ...overrides,
})

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

describe('Admin Students - 批量禁用毕业生账号（多选）', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    holder.paginated = makePaginated()
  })

  it('渲染"批量禁用毕业生账号"按钮', () => {
    const wrapper = createWrapper()
    const btn = wrapper.find('[data-testid="disable-by-class-btn"]')
    expect(btn.exists()).toBe(true)
    expect(btn.text()).toContain('批量禁用毕业生账号')
  })

  it('点击按钮打开弹窗并展示班级复选框（不含"全部班级"）', async () => {
    const wrapper = createWrapper()
    const dialog = await openDialog(wrapper)

    expect(dialog.exists()).toBe(true)
    expect(dialog.find('h3').text()).toBe('批量禁用毕业生账号')

    const checkboxes = dialog.findAll('input[type="checkbox"]')
    expect(checkboxes).toHaveLength(2)
    expect(dialog.text()).toContain('2026届软件工程1班')
    expect(dialog.text()).toContain('2026届软件工程2班')
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

    expect(holder.disableByClass).toHaveBeenCalledWith([1])
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

    expect(holder.disableByClass).toHaveBeenCalledWith([1, 2])
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

    expect(holder.disableByClass).toHaveBeenCalledWith([2])
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

describe('Admin Students - 列表分页', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('totalPages > 1 时渲染分页组件并显示总数', () => {
    holder.paginated = makePaginated({
      page: ref(1),
      total: ref(120),
      totalPages: ref(3),
    })
    const wrapper = createWrapper()

    const pagination = wrapper.find('[data-testid="students-pagination"]')
    expect(pagination.exists()).toBe(true)
    expect(pagination.text()).toContain('1 / 3')
    expect(pagination.text()).toContain('共 120 人')
  })

  it('totalPages <= 1 时不渲染分页组件', () => {
    holder.paginated = makePaginated({
      total: ref(30),
      totalPages: ref(1),
    })
    const wrapper = createWrapper()

    expect(wrapper.find('[data-testid="students-pagination"]').exists()).toBe(false)
  })

  it('点击下一页/上一页切换页码', async () => {
    const page = ref(1)
    holder.paginated = makePaginated({
      page,
      total: ref(120),
      totalPages: ref(3),
    })
    const wrapper = createWrapper()

    // 第一页时上一页禁用
    expect(wrapper.find('[data-testid="students-prev-page"]').attributes('disabled')).toBeDefined()

    await wrapper.find('[data-testid="students-next-page"]').trigger('click')
    expect(page.value).toBe(2)

    await wrapper.find('[data-testid="students-prev-page"]').trigger('click')
    expect(page.value).toBe(1)
  })

  it('最后一页时下一页禁用', () => {
    holder.paginated = makePaginated({
      page: ref(3),
      total: ref(120),
      totalPages: ref(3),
    })
    const wrapper = createWrapper()

    expect(wrapper.find('[data-testid="students-next-page"]').attributes('disabled')).toBeDefined()
    expect(wrapper.find('[data-testid="students-prev-page"]').attributes('disabled')).toBeUndefined()
  })

  it('搜索模式下不显示分页组件，显示匹配数量', () => {
    const fakeStudent = (id: string) => ({
      student_id: id,
      name: `学生${id}`,
      class_name: '一班',
      score: 80,
      is_account_enabled: true,
      checkin_status: 'not_checked_in',
    })
    holder.paginated = makePaginated({
      isSearching: ref(true),
      filteredStudents: ref([fakeStudent('S001'), fakeStudent('S002')]),
      totalPages: ref(3),
    })
    const wrapper = createWrapper()

    expect(wrapper.find('[data-testid="students-pagination"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('找到 2 名匹配的学生')
  })
})
