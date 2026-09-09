/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Semesters from '@/views/admin/Semesters.vue'

vi.mock('@/api/semesters', () => ({
  semestersApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    activate: vi.fn(),
    rollover: vi.fn(),
  },
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ showToast: vi.fn() }),
}))

import { semestersApi } from '@/api/semesters'
const mockedList = vi.mocked(semestersApi.list)
const mockedActivate = vi.mocked(semestersApi.activate)

const fakeSemester = (id: number, label: string, isCurrent = false) => ({
  id,
  label,
  start_date: '2026-09-07',
  total_weeks: 20,
  is_current: isCurrent,
  status: 'active' as const,
})

// Stub Dialog 避免 Teleport 到 body 无法断言
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
  return mount(Semesters, {
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

describe('Semesters 学期管理', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedList.mockResolvedValue([
      fakeSemester(1, '2026-2027-1', true),
      fakeSemester(2, '2025-2026-2'),
    ])
  })

  it('渲染学期列表与当前学期标记', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('2026-2027-1')
    expect(wrapper.text()).toContain('2025-2026-2')
    expect(wrapper.text()).toContain('当前')
  })

  it('点击创建按钮打开创建弹窗', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const createButton = wrapper.findAll('button').find((b) => b.text().includes('创建学期'))
    expect(createButton).toBeTruthy()
    await createButton!.trigger('click')
    await flushPromises()

    expect(wrapper.find('.mock-dialog').exists()).toBe(true)
    expect(wrapper.text()).toContain('如 2026-2027-1')
  })

  it('非当前学期显示设为当前，确认后调用 activate', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const activateButton = wrapper.findAll('button').find((b) => b.text().includes('设为当前'))
    expect(activateButton).toBeTruthy()
    await activateButton!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('切换当前学期')

    mockedActivate.mockResolvedValue(undefined)
    const confirmButton = wrapper.findAll('button').find((b) => b.text().includes('确认切换'))
    await confirmButton!.trigger('click')
    await flushPromises()

    expect(mockedActivate).toHaveBeenCalledWith(2)
  })
})
