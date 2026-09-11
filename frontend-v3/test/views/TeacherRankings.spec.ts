/**
 * @vitest-environment jsdom
 *
 * 教师端排行榜：4 榜（个人/小组 × 班内/跨班）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import TeacherRankings from '@/views/teacher/TeacherRankings.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
}))

vi.mock('@/api/rankings', () => ({
  rankingsApi: {
    getRankings: vi.fn(),
  },
}))

vi.mock('@/api/offerings', () => ({
  offeringsApi: {
    listMine: vi.fn(() => Promise.resolve([
      { id: 1, course_id: 1, course_name: '高等数学', course_code: 'MATH1', teacher_name: '张老师', class_scope: '一班', capacity: null, status: 'active', enrolled_count: 2 },
    ])),
  },
}))

// 班内榜班级下拉需要按 display_name 反查 class_id
vi.mock('@/api/classes', () => ({
  classesApi: {
    list: vi.fn(() => Promise.resolve([
      { id: 1, name: '1班', major: '软件工程', cohort_year: '2026', display_name: '2026届软件工程1班', student_count: 0, status: 'active' },
      { id: 2, name: '2班', major: '软件工程', cohort_year: '2026', display_name: '2026届软件工程2班', student_count: 0, status: 'active' },
    ])),
  },
}))

import { rankingsApi } from '@/api/rankings'
const mockedGetRankings = vi.mocked(rankingsApi.getRankings)

const individualData = {
  type: 'individual' as const,
  scope: 'class' as const,
  course_name: '高等数学',
  classes: ['2026届软件工程1班'],
  entries: [
    { rank: 1, student_id: 'S001', name: '张三', class_name: '2026届软件工程1班', score: 90 },
    { rank: 2, student_id: 'S002', name: '李四', class_name: '2026届软件工程1班', score: 80 },
  ],
  my_rank: null,
}

const groupData = {
  type: 'group' as const,
  scope: 'class' as const,
  course_name: '高等数学',
  classes: ['2026届软件工程1班'],
  entries: [
    { rank: 1, group_id: 1, name: '第一组', class_name: '2026届软件工程1班', score: 95, members: ['张三', '李四'] },
  ],
  my_rank: null,
}

const MockCard = { template: '<div class="mock-card"><slot /></div>' }

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
  return mount(TeacherRankings, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Card: MockCard,
        Button: MockButton,
        Select: MockSelect,
      },
    },
  })
}

const selectCourse = async (wrapper: Awaited<ReturnType<typeof mountComponent>>) => {
  const select = wrapper.find('.mock-select')
  await select.setValue('1')
  await flushPromises()
}

describe('TeacherRankings 教师排行榜', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedGetRankings.mockResolvedValue(individualData)
  })

  it('未选择科目时显示提示', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('请选择科目')
    expect(mockedGetRankings).not.toHaveBeenCalled()
  })

  it('选择科目后查询个人班内榜并渲染', async () => {
    const wrapper = mountComponent()
    await flushPromises()
    await selectCourse(wrapper)

    expect(mockedGetRankings).toHaveBeenLastCalledWith({
      type: 'individual', course_id: 1, scope: 'class', class_id: 1,
    })
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('90')
  })

  it('切换到小组成绩后展示成员名单', async () => {
    mockedGetRankings.mockResolvedValue(groupData)
    const wrapper = mountComponent()
    await flushPromises()
    await selectCourse(wrapper)

    const groupButton = wrapper.findAll('button').find((b) => b.text().includes('小组成绩'))
    await groupButton!.trigger('click')
    await flushPromises()

    expect(mockedGetRankings).toHaveBeenLastCalledWith({
      type: 'group', course_id: 1, scope: 'class', class_id: 1,
    })
    expect(wrapper.text()).toContain('第一组')
    expect(wrapper.text()).toContain('张三、李四')
  })

  it('切换到跨班后按 all 范围查询', async () => {
    mockedGetRankings.mockResolvedValue({
      ...individualData,
      scope: 'all' as const,
      classes: ['2026届软件工程1班', '2026届软件工程2班'],
    })
    const wrapper = mountComponent()
    await flushPromises()
    await selectCourse(wrapper)

    const allButton = wrapper.findAll('button').find((b) => b.text().includes('跨班'))
    await allButton!.trigger('click')
    await flushPromises()

    expect(mockedGetRankings).toHaveBeenLastCalledWith({
      type: 'individual', course_id: 1, scope: 'all', class_id: undefined,
    })
  })
})
