/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import MyOfferings from '@/views/teacher/MyOfferings.vue'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

vi.mock('@/api/offerings', () => ({
  offeringsApi: {
    listMine: vi.fn(),
  },
}))

import { offeringsApi } from '@/api/offerings'
const mockedListMine = vi.mocked(offeringsApi.listMine)

const fakeOffering = (id: number, name = '高等数学', scope = '一班') => ({
  id,
  course_id: 1,
  course_name: name,
  course_code: 'MATH1',
  teacher_name: '张老师',
  class_scope: scope,
  capacity: 60,
  status: 'active' as const,
  enrolled_count: 30,
})

const MockCard = { template: '<div class="mock-card"><slot /></div>' }

const MockBadge = {
  props: ['variant'],
  template: '<span class="mock-badge"><slot /></span>',
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

const createTestQueryClient = () => new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

const mountComponent = () => {
  const queryClient = createTestQueryClient()
  return mount(MyOfferings, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Card: MockCard,
        Badge: MockBadge,
        Button: MockButton,
      },
    },
  })
}

describe('MyOfferings 我的教学班', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedListMine.mockResolvedValue([
      fakeOffering(1),
      fakeOffering(2, '大学物理', '二班'),
    ])
  })

  it('渲染授课列表（课程/范围/人数/状态）', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('高等数学')
    expect(wrapper.text()).toContain('大学物理')
    expect(wrapper.text()).toContain('30')
    expect(wrapper.text()).toContain('开课中')
  })

  it('点击成绩录入跳转成绩页', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const gradeButtons = wrapper.findAll('button').filter((b) => b.text().includes('成绩录入'))
    await gradeButtons[0]!.trigger('click')

    expect(mockPush).toHaveBeenCalledWith('/teacher/offerings/1/grades')
  })

  it('点击排行榜跳转排行榜页并携带科目', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const rankButtons = wrapper.findAll('button').filter((b) => b.text().includes('排行榜'))
    await rankButtons[0]!.trigger('click')

    expect(mockPush).toHaveBeenCalledWith({ path: '/teacher/rankings', query: { course_id: '1' } })
  })

  it('无授课任务时显示空状态', async () => {
    mockedListMine.mockResolvedValue([])
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('本学期暂无授课任务')
  })
})
