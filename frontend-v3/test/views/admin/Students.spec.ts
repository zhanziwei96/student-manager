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
  disableByClass: vi.fn(() => Promise.resolve({ disabled_count: 3, class_names: ['一班'] })),
  getSubjects: vi.fn(),
  updateSubjectScore: vi.fn(() => Promise.resolve()),
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
    getSubjects: holder.getSubjects,
    updateSubjectScore: holder.updateSubjectScore,
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
  className: ref(''),
  isSearching: ref(false),
  classOptions: ref([
    { value: '', label: '全部班级', count: 0 },
    { value: '一班', label: '一班', count: 0 },
    { value: '二班', label: '二班', count: 0 },
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
    expect(dialog.text()).toContain('一班')
    expect(dialog.text()).toContain('二班')
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

describe('Admin Students - 科目分数展示', () => {
  const fakeStudent = {
    student_id: 'S001',
    name: '小明',
    class_name: '一班',
    score: 175,
    is_account_enabled: true,
    checkin_status: 'not_checked_in',
  }

  const fakeSubjectScores = [
    { subject_id: 1, subject_name: '数学', teacher_id: 1, teacher_name: '张老师', score: 90 },
    { subject_id: 2, subject_name: '语文', teacher_id: 2, teacher_name: '李老师', score: 85 },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    holder.getSubjects.mockResolvedValue(fakeSubjectScores)
    holder.paginated = makePaginated({
      filteredStudents: ref([fakeStudent]),
      total: ref(1),
    })
  })

  it('点击"科目分数"按钮展开行并显示该学生所有科目分数', async () => {
    const wrapper = createWrapper()

    await wrapper.find('[data-testid="expand-subjects-btn"]').trigger('click')
    await flushPromises()

    expect(holder.getSubjects).toHaveBeenCalledWith('S001')

    const row = wrapper.find('[data-testid="subject-scores-row"]')
    expect(row.exists()).toBe(true)

    const items = row.findAll('[data-testid="subject-score-item"]')
    expect(items).toHaveLength(2)
    expect(row.text()).toContain('数学')
    expect(row.text()).toContain('90')
    expect(row.text()).toContain('张老师')
    expect(row.text()).toContain('语文')
    expect(row.text()).toContain('李老师')
  })

  it('再次点击按钮收起展开行', async () => {
    const wrapper = createWrapper()

    await wrapper.find('[data-testid="expand-subjects-btn"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="subject-scores-row"]').exists()).toBe(true)

    await wrapper.find('[data-testid="expand-subjects-btn"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="subject-scores-row"]').exists()).toBe(false)
  })

  it('无科目分数记录时显示空态文案', async () => {
    holder.getSubjects.mockResolvedValue([])
    const wrapper = createWrapper()

    await wrapper.find('[data-testid="expand-subjects-btn"]').trigger('click')
    await flushPromises()

    const row = wrapper.find('[data-testid="subject-scores-row"]')
    expect(row.text()).toContain('暂无科目分数记录')
  })

  it('展开后打开科目分数调整弹窗，默认选中第一个科目', async () => {
    const wrapper = createWrapper()

    await wrapper.find('[data-testid="expand-subjects-btn"]').trigger('click')
    await flushPromises()
    await wrapper.find('[data-testid="open-subject-score-dialog-btn"]').trigger('click')
    await flushPromises()

    const dialogs = wrapper.findAll('.mock-dialog')
    const scoreDialog = dialogs[dialogs.length - 1]
    expect(scoreDialog.find('h3').text()).toBe('调整 小明 的科目分数')
    expect(scoreDialog.text()).toContain('数学（当前 90 分）')
    expect(scoreDialog.text()).toContain('语文（当前 85 分）')
  })

  it('填写原因后提交调用 updateSubjectScore 并显示成功提示', async () => {
    const wrapper = createWrapper()

    await wrapper.find('[data-testid="expand-subjects-btn"]').trigger('click')
    await flushPromises()
    await wrapper.find('[data-testid="open-subject-score-dialog-btn"]').trigger('click')
    await flushPromises()

    const dialogs = wrapper.findAll('.mock-dialog')
    const scoreDialog = dialogs[dialogs.length - 1]
    await scoreDialog.find('#subjectScoreChange').setValue(5)
    await scoreDialog.find('#subjectScoreReason').setValue('课堂表现优秀')
    await scoreDialog.find('[data-testid="confirm-subject-score-btn"]').trigger('click')
    await flushPromises()

    expect(holder.updateSubjectScore).toHaveBeenCalledWith('S001', 1, 5, '课堂表现优秀')
    expect(holder.success).toHaveBeenCalledWith('小明 的科目分数已更新')
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
