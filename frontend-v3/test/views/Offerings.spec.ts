/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises, type DOMWrapper } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Offerings from '@/views/admin/Offerings.vue'

vi.mock('@/api/offerings', () => ({
  offeringsApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    listEnrollments: vi.fn(),
    importEnrollments: vi.fn(),
    enrollByClass: vi.fn(),
    dropEnrollment: vi.fn(),
  },
}))

vi.mock('@/api/classes', () => ({
  classesApi: {
    list: vi.fn(() => Promise.resolve([
      { id: 1, name: '1班', major: '计算机科学与技术', cohort_year: '2026', display_name: '2026届计算机科学与技术1班', student_count: 0, status: 'active' },
      { id: 2, name: '2班', major: '计算机科学与技术', cohort_year: '2026', display_name: '2026届计算机科学与技术2班', student_count: 0, status: 'active' },
      { id: 3, name: '1班', major: '软件工程', cohort_year: '2025', display_name: '2025届软件工程1班', student_count: 0, status: 'active' },
    ])),
  },
}))

vi.mock('@/api/courses', () => ({
  coursesApi: {
    list: vi.fn(() => Promise.resolve([
      { id: 1, code: 'MATH1', name: '高等数学', department: '', status: 'active' },
    ])),
  },
}))

vi.mock('@/api/semesters', () => ({
  semestersApi: {
    list: vi.fn(() => Promise.resolve([
      { id: 1, label: '2026-2027-1', start_date: '2026-09-07', total_weeks: 20, is_current: true, status: 'active' },
    ])),
  },
}))

vi.mock('@/api/users', () => ({
  usersApi: {
    getTeachers: vi.fn(() => Promise.resolve([
      { id: 1, username: 't1', name: '张老师', role: 'teacher', is_account_enabled: true },
    ])),
  },
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ showToast: vi.fn() }),
}))

import { offeringsApi } from '@/api/offerings'
const mockedList = vi.mocked(offeringsApi.list)
const mockedListEnrollments = vi.mocked(offeringsApi.listEnrollments)
const mockedCreate = vi.mocked(offeringsApi.create)
const mockedUpdate = vi.mocked(offeringsApi.update)

const fakeOffering = (id: number, classIds: number[] = [1, 2]) => ({
  id,
  course_id: 1,
  semester_id: 1,
  teacher_id: 1,
  teacher_name: '张老师',
  class_scope: '计科1-2班',
  class_ids: classIds,
  capacity: 60,
  status: 'active' as const,
})

const MockDialog = {
  name: 'Dialog',
  props: ['open', 'title', 'description'],
  emits: ['update:open'],
  template: `
    <div v-if="open" class="mock-dialog">
      <h3>{{ title }}</h3>
      <p>{{ description }}</p>
      <slot />
      <slot name="footer" />
    </div>
  `,
}

const MockButton = {
  name: 'Button',
  props: ['type', 'variant', 'size', 'disabled'],
  emits: ['click'],
  template: `
    <button :type="type || 'button'" :disabled="disabled" @click="$emit('click')">
      <slot />
    </button>
  `,
}

const MockCard = { template: '<div class="mock-card"><slot /></div>' }

const MockBadge = {
  props: ['variant'],
  template: '<span class="mock-badge"><slot /></span>',
}

const MockInput = {
  name: 'Input',
  props: ['modelValue', 'type', 'placeholder'],
  emits: ['update:modelValue'],
  template: '<input :value="modelValue" :type="type || \'text\'" :placeholder="placeholder" class="mock-input" />',
}

const MockSelect = {
  name: 'Select',
  props: ['modelValue', 'options', 'placeholder'],
  emits: ['update:modelValue'],
  template: `
    <select :value="modelValue" class="mock-select" @change="$emit('update:modelValue', $event.target.value)">
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option v-for="opt in options || []" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
  `,
}

const createTestQueryClient = () => new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

const mountComponent = () => {
  const queryClient = createTestQueryClient()
  return mount(Offerings, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Dialog: MockDialog,
        Button: MockButton,
        Card: MockCard,
        Badge: MockBadge,
        Input: MockInput,
        Select: MockSelect,
      },
    },
  })
}

type Wrapper = ReturnType<typeof mountComponent>

/** 打开创建弹窗（课程/学期已填好，可直接提交） */
const openCreateDialog = async (wrapper: Wrapper) => {
  const createButton = wrapper.findAll('button').find((b) => b.text().includes('创建教学班'))
  await createButton!.trigger('click')
  await flushPromises()
  const dialog = wrapper.find('.mock-dialog')
  await dialog.findAll('select')[0].setValue('1')
  await flushPromises()
  return dialog
}

/** 打开编辑弹窗 */
const openEditDialog = async (wrapper: Wrapper) => {
  await wrapper.find('[data-testid="edit-offering-btn"]').trigger('click')
  await flushPromises()
  return wrapper.find('.mock-dialog')
}

/** 弹窗内班级复选框（按渲染顺序） */
const classCheckboxes = (dialog: DOMWrapper<Element>) =>
  dialog.findAll('input[type="checkbox"]')

/** 点击弹窗底部提交按钮（文案「创建」/「保存」） */
const submit = async (wrapper: Wrapper, label: string) => {
  const button = wrapper.findAll('.mock-dialog button').find((b) => b.text().trim() === label)!
  await button.trigger('click')
  await flushPromises()
}

describe('Offerings 教学班管理', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedList.mockResolvedValue([fakeOffering(1)])
    mockedCreate.mockResolvedValue(fakeOffering(2))
    mockedUpdate.mockResolvedValue(fakeOffering(1))
    mockedListEnrollments.mockResolvedValue([
      { enrollment_id: 1, student_id: 'S001', name: '学生1', class_name: '一班', score: 85, final_score: null },
    ])
  })

  it('渲染教学班列表（课程名/教师/范围/状态）', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(mockedList).toHaveBeenCalledWith(1) // 缺省当前学期
    expect(wrapper.text()).toContain('高等数学')
    expect(wrapper.text()).toContain('张老师')
    expect(wrapper.text()).toContain('计科1-2班')
    expect(wrapper.text()).toContain('开课中')
  })

  it('点击创建按钮打开创建弹窗', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const createButton = wrapper.findAll('button').find((b) => b.text().includes('创建教学班'))
    await createButton!.trigger('click')
    await flushPromises()

    expect(wrapper.find('.mock-dialog').exists()).toBe(true)
    expect(wrapper.text()).toContain('面向范围')
  })

  it('创建弹窗展示按届/专业分组的班级多选，未选班级提示「全部班级」', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const dialog = await openCreateDialog(wrapper)

    expect(dialog.text()).toContain('2026届 · 计算机科学与技术')
    expect(dialog.text()).toContain('2025届 · 软件工程')
    expect(classCheckboxes(dialog)).toHaveLength(3)
    expect(dialog.text()).toContain('未选择班级 = 面向全部班级（通配）')
  })

  it('选择两个班级后创建 → class_ids 为所选班级', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const dialog = await openCreateDialog(wrapper)
    await classCheckboxes(dialog)[0].setValue(true)
    await classCheckboxes(dialog)[1].setValue(true)
    await flushPromises()
    expect(dialog.text()).toContain('已选 2 个班级')

    await submit(wrapper, '创建')

    expect(mockedCreate).toHaveBeenCalledWith({
      course_id: 1,
      semester_id: 1,
      teacher_id: null,
      class_ids: [1, 2],
      capacity: null,
    })
  })

  it('不选择班级创建 → class_ids 为空数组（全部班级通配）', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    await openCreateDialog(wrapper)
    await submit(wrapper, '创建')

    expect(mockedCreate).toHaveBeenCalledWith({
      course_id: 1,
      semester_id: 1,
      teacher_id: null,
      class_ids: [],
      capacity: null,
    })
  })

  it('「全选」选中全部班级，再点「清空」回到全部班级通配', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const dialog = await openCreateDialog(wrapper)
    await dialog.find('[data-testid="create-select-all-classes"]').trigger('click')
    await flushPromises()
    expect(dialog.text()).toContain('已选 3 个班级')

    await dialog.find('[data-testid="create-select-all-classes"]').trigger('click')
    await flushPromises()
    expect(dialog.text()).toContain('未选择班级 = 面向全部班级（通配）')
  })

  it('编辑弹窗回显已有班级并按提交内容更新 class_ids', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const dialog = await openEditDialog(wrapper)
    expect(classCheckboxes(dialog)[0].element).toHaveProperty('checked', true)
    expect(classCheckboxes(dialog)[2].element).toHaveProperty('checked', false)

    // 取消勾选 2 班 → 仅剩 [1]
    await classCheckboxes(dialog)[1].setValue(false)
    await flushPromises()
    await submit(wrapper, '保存')

    expect(mockedUpdate).toHaveBeenCalledWith(1, {
      teacher_id: 1,
      class_ids: [1],
      capacity: 60,
    })
  })

  it('打开名单弹窗显示选课学生', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const rosterButton = wrapper.findAll('button').find((b) => b.text().includes('名单'))
    await rosterButton!.trigger('click')
    await flushPromises()

    expect(mockedListEnrollments).toHaveBeenCalledWith(1)
    expect(wrapper.text()).toContain('S001')
    expect(wrapper.text()).toContain('学生1')
    expect(wrapper.text()).toContain('退课')
  })

  it('名单弹窗可按班级一键加入名单', async () => {
    const mockedEnrollByClass = vi.mocked(offeringsApi.enrollByClass)
    mockedEnrollByClass.mockResolvedValue({ imported: 28, skipped: 0 })

    const wrapper = mountComponent()
    await flushPromises()

    const rosterButton = wrapper.findAll('button').find((b) => b.text().includes('名单'))
    await rosterButton!.trigger('click')
    await flushPromises()

    // 未选班级时按钮禁用
    const enrollBtn = wrapper.find('[data-testid="enroll-by-class"]')
    expect(enrollBtn.exists()).toBe(true)
    expect(enrollBtn.attributes('disabled')).toBeDefined()

    // 选择班级（display_name 作为选项文案）后点击 → 调用 API
    const classSelect = wrapper
      .findAll('select')
      .find((el) => el.findAll('option').some((o) => o.text().includes('2025届软件工程1班')))
    expect(classSelect).toBeTruthy()
    await classSelect!.setValue('3')
    await flushPromises()

    await wrapper.find('[data-testid="enroll-by-class"]').trigger('click')
    await flushPromises()

    expect(mockedEnrollByClass).toHaveBeenCalledWith(1, [3])
  })
})
