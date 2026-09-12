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

const fakeRow = (id: number, sid: string, name: string, className: string | null = '一班') => ({
  enrollment_id: id,
  student_id: sid,
  name,
  class_name: className,
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
  // 与真实 Input 一致：number 类型回传数值，其余回传字符串
  template: `<input
    :value="modelValue"
    :type="type || 'text'"
    :placeholder="placeholder"
    class="mock-input"
    @input="$emit('update:modelValue', type === 'number' ? Number($event.target.value) : $event.target.value)"
  />`,
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

  const mockRoster = () => mockedListEnrollments.mockResolvedValue([
    fakeRow(1, 'S001', '张三', '2026届软件工程一班'),
    fakeRow(2, 'S002', '李四', '2026届软件工程一班'),
    fakeRow(3, 'S003', '王五', '2026届软件工程二班'),
  ])

  it('名单按行政班分组，组标题带人数', async () => {
    mockRoster()
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('2026届软件工程一班')
    expect(wrapper.text()).toContain('2026届软件工程二班')
    expect(wrapper.text()).toContain('2 人')
    expect(wrapper.text()).toContain('1 人')
  })

  it('搜索学号或姓名过滤名单并提示筛选人数', async () => {
    mockRoster()
    const wrapper = mountComponent()
    await flushPromises()

    const search = () => wrapper.find('input[placeholder="搜索学号或姓名..."]')

    await search().setValue('王五')  // 按姓名
    await flushPromises()
    expect(wrapper.text()).toContain('王五')
    expect(wrapper.text()).not.toContain('张三')
    expect(wrapper.text()).toContain('筛选出 1 人')

    await search().setValue('S001')  // 按学号
    await flushPromises()
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).not.toContain('王五')
  })

  it('班级筛选只显示该班学生', async () => {
    mockRoster()
    const wrapper = mountComponent()
    await flushPromises()

    await wrapper.find('select.mock-select').setValue('2026届软件工程二班')
    await flushPromises()

    expect(wrapper.text()).toContain('王五')
    expect(wrapper.text()).not.toContain('张三')
  })

  it('无匹配时提示空结果，清空后恢复', async () => {
    mockRoster()
    const wrapper = mountComponent()
    await flushPromises()

    const search = wrapper.find('input[placeholder="搜索学号或姓名..."]')
    await search.setValue('不存在的学生')
    await flushPromises()
    expect(wrapper.text()).toContain('没有匹配的学生')

    await search.setValue('')
    await flushPromises()
    expect(wrapper.text()).toContain('张三')
  })

  it('班级缺失的行归入「未分班」，不丢行', async () => {
    mockedListEnrollments.mockResolvedValue([
      fakeRow(1, 'S001', '张三', null),
      fakeRow(2, 'S002', '李四', '2026届软件工程一班'),
    ])
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('未分班')
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('李四')
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

  it('快捷标签同时填入原因与分值，保存后带上该分值', async () => {
    const wrapper = mountComponent()
    await flushPromises()
    mockedUpdateScore.mockResolvedValue({ enrollment_id: 1, score: 82 })

    const scoreButtons = wrapper.findAll('button').filter((b) => b.text().includes('加减分'))
    await scoreButtons[0]!.trigger('click')
    await flushPromises()

    await wrapper.find('[data-testid="score-preset-课堂积极发言"]').trigger('click')
    await flushPromises()

    const reasonInput = wrapper.find('input[placeholder="如：课堂表现优秀"]').element as HTMLInputElement
    const deltaInput = wrapper.find('input[type="number"]').element as HTMLInputElement
    expect(reasonInput.value).toBe('课堂积极发言')
    expect(deltaInput.value).toBe('2')

    await wrapper.findAll('button').find((b) => b.text().includes('保存'))!.trigger('click')
    await flushPromises()

    expect(mockedUpdateScore).toHaveBeenCalledWith(1, { score_change: 2, reason: '课堂积极发言' })
  })

  it('减分标签填入负分（旷课 -5）', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const scoreButtons = wrapper.findAll('button').filter((b) => b.text().includes('加减分'))
    await scoreButtons[0]!.trigger('click')
    await flushPromises()

    await wrapper.find('[data-testid="score-preset-旷课"]').trigger('click')
    await flushPromises()

    const deltaInput = wrapper.find('input[type="number"]').element as HTMLInputElement
    expect(deltaInput.value).toBe('-5')
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
