/**
 * @vitest-environment jsdom
 *
 * 管理员学生管理页：学籍状态切换与转班
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import AdminStudents from '@/views/admin/Students.vue'

const fakeStudent = (id: string, name: string, className = '一班', status = 'active') => ({
  student_id: id,
  name,
  class_name: className,
  score: 80,
  status,
  is_account_enabled: true,
  checkin_status: 'not_checked_in' as const,
})

const mockStudents = ref([
  fakeStudent('S001', '张三', '一班', 'active'),
  fakeStudent('S002', '李四', '二班', 'suspended'),
])

// Mock 共享 composable（分页逻辑在 usePaginatedStudents.spec 覆盖）
vi.mock('@/features/students', () => ({
  usePaginatedStudents: () => ({
    page: ref(1),
    searchQuery: ref(''),
    className: ref(''),
    isSearching: ref(false),
    classOptions: ref([
      { value: '', label: '全部班级', count: 0 },
      { value: '一班', label: '一班', count: 0 },
      { value: '二班', label: '二班', count: 0 },
    ]),
    filteredStudents: mockStudents,
    total: ref(2),
    totalPages: ref(1),
    isPending: ref(false),
    error: ref(null),
    refetch: vi.fn(),
    setSearchQuery: vi.fn(),
    setClassFilter: vi.fn(),
  }),
  StudentFilters: {
    props: ['searchQuery', 'selectedClass', 'classOptions', 'selectedCohort', 'cohortOptions'],
    emits: ['update:searchQuery', 'update:selectedClass', 'update:selectedCohort'],
    template: '<div class="mock-student-filters"><slot /></div>',
  },
}))

vi.mock('@/composables', () => ({
  useStudentCreate: () => ({ mutateAsync: vi.fn(), isPending: ref(false) }),
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('@/api', () => ({
  studentsApi: {
    updateStatus: vi.fn(),
    transferClass: vi.fn(),
    disableByClass: vi.fn(),
  },
}))

vi.mock('@/api/classes', () => ({
  classesApi: {
    list: vi.fn(() => Promise.resolve([])),
  },
}))

vi.mock('@/api/cohorts', () => ({
  cohortsApi: {
    list: vi.fn(() => Promise.resolve([{ year: '2026', label: '2026届', entry_semester_id: null, status: 'active' }])),
  },
}))

import { studentsApi } from '@/api'
const mockedUpdateStatus = vi.mocked(studentsApi.updateStatus)
const mockedTransferClass = vi.mocked(studentsApi.transferClass)

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
  props: ['type', 'variant', 'size', 'disabled', 'loading'],
  emits: ['click'],
  template: `
    <button :type="type || 'button'" :disabled="disabled" @click="$emit('click')">
      <slot />
    </button>
  `,
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

const MockBadge = {
  props: ['variant'],
  template: '<span class="mock-badge"><slot /></span>',
}

const createTestQueryClient = () => new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

const mountComponent = () => {
  const queryClient = createTestQueryClient()
  return mount(AdminStudents, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Dialog: MockDialog,
        Button: MockButton,
        Select: MockSelect,
        Badge: MockBadge,
        Card: { template: '<div class="mock-card"><slot /></div>' },
        Input: {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template: '<input :value="modelValue" class="mock-input" />',
        },
        Label: { template: '<label><slot /></label>' },
        Checkbox: { props: ['checked'], template: '<input type="checkbox" :checked="checked" />' },
        DataContainer: { template: '<div class="mock-data-container"><slot /></div>' },
      },
    },
  })
}

describe('AdminStudents 学籍与转班', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('渲染学生列表与学籍状态标记', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('在读')
    expect(wrapper.text()).toContain('休学')
  })

  it('打开学籍弹窗并保存调用 updateStatus', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    mockedUpdateStatus.mockResolvedValue(undefined)
    const statusButtons = wrapper.findAll('button').filter((b) => b.text().trim() === '学籍')
    await statusButtons[0]!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('调整 张三 的学籍状态')

    const confirmButton = wrapper.findAll('button').find((b) => b.text().trim() === '保存')
    await confirmButton!.trigger('click')
    await flushPromises()

    expect(mockedUpdateStatus).toHaveBeenCalledWith('S001', 'active')
  })

  it('打开转班弹窗并确认调用 transferClass', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    mockedTransferClass.mockResolvedValue(undefined)
    const transferButtons = wrapper.findAll('button').filter((b) => b.text().trim() === '转班')
    await transferButtons[0]!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('张三 转班')
    expect(wrapper.text()).toContain('当前班级：一班')

    // 选择目标班级（届 → 班级联动，此处直接触发确认前需要选择）
    const confirmButton = wrapper.findAll('button').find((b) => b.text().includes('确认转班'))
    await confirmButton!.trigger('click')
    await flushPromises()

    // 未选择班级时提示错误，不调用 API
    expect(mockedTransferClass).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('请选择目标班级')
  })
})
