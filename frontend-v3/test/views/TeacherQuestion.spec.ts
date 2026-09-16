/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import TeacherQuestion from '@/views/teacher/TeacherQuestion.vue'

vi.mock('@/api/question', () => ({
  getTeacherQuestions: vi.fn(() => Promise.resolve([])),
  createQuestion: vi.fn(() => Promise.resolve({ question_id: 1 })),
  closeQuestion: vi.fn(() => Promise.resolve()),
  replyAnswer: vi.fn(() => Promise.resolve({ answer_id: 1 })),
  starAnswer: vi.fn(() => Promise.resolve()),
  getStudentQuestions: vi.fn(() => Promise.resolve([])),
  getAnswers: vi.fn(() => Promise.resolve([])),
  createAnswer: vi.fn(() => Promise.resolve({ answer_id: 1 })),
  updateAnswer: vi.fn(() => Promise.resolve({ answer_id: 1 })),
  deleteAnswer: vi.fn(() => Promise.resolve()),
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

import { createQuestion } from '@/api/question'
const mockedCreate = vi.mocked(createQuestion)

const createTestQueryClient = () => new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

const mountComponent = () => {
  const queryClient = createTestQueryClient()
  return mount(TeacherQuestion, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        QuestionCard: true,
        AnswerList: true,
        AnswerInput: true,
        PullToRefreshIndicator: true,
      },
    },
  })
}

type Wrapper = ReturnType<typeof mountComponent>

/** 打开发布表单并填好问题内容 */
const openCreateForm = async (wrapper: Wrapper) => {
  const toggleButton = wrapper.findAll('button').find((b) => b.text().includes('发布问题'))
  await toggleButton!.trigger('click')
  await flushPromises()
  await wrapper.find('textarea').setValue('今天讲什么？')
  await flushPromises()
}

/** 班级面板内复选框（按渲染顺序：2026届计科1班、2班 → 2025届软工1班） */
const classCheckboxes = (wrapper: Wrapper) =>
  wrapper.find('[data-testid="question-class-panel"]').findAll('input[type="checkbox"]')

/** 点击「发布」提交按钮 */
const submit = async (wrapper: Wrapper) => {
  const submitButton = wrapper.findAll('button').find((b) => b.text().trim() === '发布')
  await submitButton!.trigger('click')
  await flushPromises()
}

describe('TeacherQuestion 发布表单班级多选', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('渲染分组多选：3 个班级复选框 + 届·专业分组标签 + 空选提示', async () => {
    const wrapper = mountComponent()
    await openCreateForm(wrapper)

    expect(classCheckboxes(wrapper)).toHaveLength(3)
    const panel = wrapper.find('[data-testid="question-class-panel"]')
    expect(panel.text()).toContain('2026届 · 计算机科学与技术')
    expect(panel.text()).toContain('2025届 · 软件工程')
    expect(wrapper.text()).toContain('未选择班级 = 所有班级可见')
  })

  it('选择两个班级后发布 → class_ids 为所选班级', async () => {
    const wrapper = mountComponent()
    await openCreateForm(wrapper)

    await classCheckboxes(wrapper)[0].setValue(true)
    await classCheckboxes(wrapper)[1].setValue(true)
    expect(wrapper.text()).toContain('已选 2 个班级')

    await submit(wrapper)
    expect(mockedCreate).toHaveBeenCalledWith({
      content: '今天讲什么？',
      class_ids: [1, 2],
      is_realtime: false,
    })
  })

  it('不选择班级发布 → class_ids 为空数组（所有班级可见）', async () => {
    const wrapper = mountComponent()
    await openCreateForm(wrapper)

    await submit(wrapper)
    expect(mockedCreate).toHaveBeenCalledWith({
      content: '今天讲什么？',
      class_ids: [],
      is_realtime: false,
    })
  })

  it('全选后再清空 → 计数与提交随之变化', async () => {
    const wrapper = mountComponent()
    await openCreateForm(wrapper)

    const toggle = () => wrapper.find('[data-testid="create-select-all-classes"]')

    await toggle().trigger('click')
    expect(wrapper.text()).toContain('已选 3 个班级')

    // 取消一个后文案回到「全选」
    await classCheckboxes(wrapper)[0].setValue(false)
    expect(wrapper.text()).toContain('已选 2 个班级')
    expect(toggle().text()).toBe('全选')

    // 再次全选后「清空」
    await toggle().trigger('click')
    expect(toggle().text()).toBe('清空')
    await toggle().trigger('click')
    expect(wrapper.text()).toContain('未选择班级 = 所有班级可见')
  })
})
