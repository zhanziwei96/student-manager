/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Offerings from '@/views/admin/Offerings.vue'

vi.mock('@/api/offerings', () => ({
  offeringsApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    listEnrollments: vi.fn(),
    importEnrollments: vi.fn(),
    dropEnrollment: vi.fn(),
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

const fakeOffering = (id: number) => ({
  id,
  course_id: 1,
  semester_id: 1,
  teacher_id: 1,
  teacher_name: '张老师',
  class_scope: '计科1-2班',
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

describe('Offerings 教学班管理', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedList.mockResolvedValue([fakeOffering(1)])
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
})
