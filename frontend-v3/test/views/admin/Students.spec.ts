/**
 * @vitest-environment jsdom
 *
 * 管理员学生管理页 - 按班级禁用（学期归档）功能测试
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
  disableByClass: vi.fn(() => Promise.resolve({ disabled_count: 3, class_name: '一班' })),
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

// Mock Select 为原生 select，便于设置值
const MockSelect = {
  name: 'Select',
  props: ['modelValue', 'options', 'placeholder'],
  emits: ['update:modelValue'],
  template: `
    <select :value="modelValue" @change="$emit('update:modelValue', $event.target.value)">
      <option v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</option>
    </select>
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
        Select: MockSelect,
        Card: { template: '<div><slot /></div>' },
        Badge: { template: '<span><slot /></span>' },
        DataContainer: { template: '<div><slot /></div>' },
      },
    },
  })
}

describe('Admin Students - 按班级禁用', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('渲染"按班级禁用"按钮', () => {
    const wrapper = createWrapper()
    const btn = wrapper.find('[data-testid="disable-by-class-btn"]')
    expect(btn.exists()).toBe(true)
    expect(btn.text()).toContain('按班级禁用')
  })

  it('点击按钮打开弹窗并展示班级选项（不含"全部班级"）', async () => {
    const wrapper = createWrapper()
    await wrapper.find('[data-testid="disable-by-class-btn"]').trigger('click')
    await flushPromises()

    const dialog = wrapper.find('.mock-dialog')
    expect(dialog.exists()).toBe(true)
    expect(dialog.find('h3').text()).toBe('按班级禁用')

    const options = dialog.findAll('select option')
    expect(options).toHaveLength(2)
    expect(options[0].text()).toContain('一班')
    expect(options[1].text()).toContain('二班')
  })

  it('确认后调用 API 并显示成功提示', async () => {
    const wrapper = createWrapper()
    await wrapper.find('[data-testid="disable-by-class-btn"]').trigger('click')
    await flushPromises()

    const dialog = wrapper.find('.mock-dialog')
    await dialog.find('select').setValue('一班')
    await dialog.find('[data-testid="confirm-disable-btn"]').trigger('click')
    await flushPromises()

    expect(holder.disableByClass).toHaveBeenCalledWith('一班')
    expect(holder.success).toHaveBeenCalledWith('已禁用 3 名学生')
    // 成功后弹窗关闭
    expect(wrapper.find('.mock-dialog').exists()).toBe(false)
  })

  it('API 失败时显示错误提示且不关闭弹窗', async () => {
    holder.disableByClass.mockRejectedValueOnce(new Error('无权限'))
    const wrapper = createWrapper()
    await wrapper.find('[data-testid="disable-by-class-btn"]').trigger('click')
    await flushPromises()

    const dialog = wrapper.find('.mock-dialog')
    await dialog.find('select').setValue('一班')
    await dialog.find('[data-testid="confirm-disable-btn"]').trigger('click')
    await flushPromises()

    expect(holder.error).toHaveBeenCalled()
    expect(wrapper.find('.mock-dialog').exists()).toBe(true)
  })
})
