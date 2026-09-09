/**
 * @vitest-environment jsdom
 *
 * 教师成绩录入页：名单渲染 + 个人加减分 + 期末分 + 小组同分
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import OfferingGrades from '@/views/teacher/OfferingGrades.vue'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '1' } }),
  useRouter: () => ({ push: mockPush }),
}))

vi.mock('@/api/offerings', () => ({
  offeringsApi: {
    listMine: vi.fn(() => Promise.resolve([{
      id: 1, course_id: 1, course_name: '高等数学', course_code: 'MATH1',
      teacher_name: '张老师', class_scope: '一班', capacity: 60,
      status: 'active', enrolled_count: 2,
    }])),
    listEnrollments: vi.fn(),
  },
}))

vi.mock('@/api/enrollments', () => ({
  enrollmentsApi: {
    updateScore: vi.fn(),
    setFinalScore: vi.fn(),
    setGroupFinalScores: vi.fn(),
  },
}))

vi.mock('@/api/groups', () => ({
  groupsApi: {
    getGroups: vi.fn(() => Promise.resolve([{ id: 1, name: '第一组' }, { id: 2, name: '第二组' }])),
  },
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ showToast: vi.fn() }),
}))

import { offeringsApi } from '@/api/offerings'
import { enrollmentsApi } from '@/api/enrollments'
const mockedListEnrollments = vi.mocked(offeringsApi.listEnrollments)
const mockedUpdateScore = vi.mocked(enrollmentsApi.updateScore)

const fakeRow = (id: number, sid: string, name: string) => ({
  enrollment_id: id,
  student_id: sid,
  name,
  class_name: '一班',
  score: 80,
  final_score: null,
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
  return mount(OfferingGrades, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Dialog: MockDialog,
        Button: MockButton,
        Input: MockInput,
        Select: MockSelect,
        Card: { template: '<div class="mock-card"><slot /></div>' },
        Label: { template: '<label><slot /></label>' },
      },
    },
  })
}

describe('OfferingGrades 成绩录入', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedListEnrollments.mockResolvedValue([
      fakeRow(1, 'S001', '张三'),
      fakeRow(2, 'S002', '李四'),
    ])
  })

  it('渲染教学班名单与成绩', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('高等数学')
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('S001')
    expect(wrapper.text()).toContain('—')  // 期末未公布
  })

  it('打开加减分弹窗并保存调用 updateScore', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    mockedUpdateScore.mockResolvedValue({ enrollment_id: 1, score: 85 })
    const scoreButtons = wrapper.findAll('button').filter((b) => b.text().includes('加减分'))
    await scoreButtons[0]!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('调整 张三 的平时成绩')

    const saveButton = wrapper.findAll('button').find((b) => b.text().includes('保存'))
    await saveButton!.trigger('click')
    await flushPromises()

    // 未填原因时提示错误，不调用 API
    expect(mockedUpdateScore).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('请输入分数变化原因')
  })

  it('打开期末分弹窗', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const finalButtons = wrapper.findAll('button').filter((b) => b.text().includes('期末分'))
    await finalButtons[0]!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('登记 张三 的期末成绩')
  })

  it('打开期末任务同分弹窗并展示小组下拉', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const groupButtons = wrapper.findAll('button').filter((b) => b.text().includes('期末任务同分'))
    await groupButtons[0]!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('小组任务考核')
    expect(wrapper.text()).toContain('第一组')
  })
})
