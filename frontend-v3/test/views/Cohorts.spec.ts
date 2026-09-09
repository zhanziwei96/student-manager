/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Cohorts from '@/views/admin/Cohorts.vue'

vi.mock('@/api/cohorts', () => ({
  cohortsApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
  },
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ showToast: vi.fn() }),
}))

import { cohortsApi } from '@/api/cohorts'
const mockedList = vi.mocked(cohortsApi.list)
const mockedUpdate = vi.mocked(cohortsApi.update)

const fakeCohort = (year: string, status: 'active' | 'graduated' = 'active') => ({
  year,
  label: `${year}届`,
  entry_semester_id: null,
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
  return mount(Cohorts, {
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

describe('Cohorts 届管理', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedList.mockResolvedValue([
      fakeCohort('2026'),
      fakeCohort('2022', 'graduated'),
    ])
  })

  it('渲染届列表与状态标记', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('2026届')
    expect(wrapper.text()).toContain('在读')
    expect(wrapper.text()).toContain('已毕业')
  })

  it('点击创建按钮打开创建弹窗', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const createButton = wrapper.findAll('button').find((b) => b.text().includes('创建届'))
    await createButton!.trigger('click')
    await flushPromises()

    expect(wrapper.find('.mock-dialog').exists()).toBe(true)
    expect(wrapper.text()).toContain('入学年份')
  })

  it('在读届可毕业归档，确认后调用 update', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const archiveButton = wrapper.findAll('button').find((b) => b.text().includes('毕业归档'))
    await archiveButton!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('毕业归档')

    mockedUpdate.mockResolvedValue(fakeCohort('2026', 'graduated'))
    const confirmButton = wrapper.findAll('button').find((b) => b.text().trim() === '归档')
    await confirmButton!.trigger('click')
    await flushPromises()

    expect(mockedUpdate).toHaveBeenCalledWith('2026', { status: 'graduated' })
  })

  it('已毕业届显示恢复按钮，点击调用 update', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    mockedUpdate.mockResolvedValue(fakeCohort('2022'))
    const restoreButton = wrapper.findAll('button').find((b) => b.text().includes('恢复'))
    await restoreButton!.trigger('click')
    await flushPromises()

    expect(mockedUpdate).toHaveBeenCalledWith('2022', { status: 'active' })
  })
})
