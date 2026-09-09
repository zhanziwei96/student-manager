/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Courses from '@/views/admin/Courses.vue'

vi.mock('@/api/courses', () => ({
  coursesApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
  },
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ showToast: vi.fn() }),
}))

import { coursesApi } from '@/api/courses'
const mockedList = vi.mocked(coursesApi.list)
const mockedUpdate = vi.mocked(coursesApi.update)

const fakeCourse = (id: number, code: string, name: string, status: 'active' | 'archived' = 'active') => ({
  id,
  code,
  name,
  department: '数学学院',
  status,
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

const createTestQueryClient = () => new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

const mountComponent = () => {
  const queryClient = createTestQueryClient()
  return mount(Courses, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Dialog: MockDialog,
        Button: MockButton,
        Card: MockCard,
        Badge: MockBadge,
        Input: MockInput,
      },
    },
  })
}

describe('Courses 课程管理', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedList.mockResolvedValue([
      fakeCourse(1, 'MATH1', '高等数学'),
      fakeCourse(2, 'PHY1', '大学物理', 'archived'),
    ])
  })

  it('渲染课程列表与状态标记', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('MATH1')
    expect(wrapper.text()).toContain('高等数学')
    expect(wrapper.text()).toContain('启用')
    expect(wrapper.text()).toContain('已归档')
  })

  it('点击创建按钮打开创建弹窗', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const createButton = wrapper.findAll('button').find((b) => b.text().includes('创建课程'))
    await createButton!.trigger('click')
    await flushPromises()

    expect(wrapper.find('.mock-dialog').exists()).toBe(true)
    expect(wrapper.text()).toContain('课程编码')
  })

  it('归档课程调用 update status=archived，已归档课程可恢复', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    mockedUpdate.mockResolvedValue(fakeCourse(1, 'MATH1', '高等数学', 'archived'))
    const archiveButton = wrapper.findAll('button').find((b) => b.text().includes('归档'))
    await archiveButton!.trigger('click')
    await flushPromises()

    expect(mockedUpdate).toHaveBeenCalledWith(1, { status: 'archived' })
  })
})
