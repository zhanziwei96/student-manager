/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Classrooms from '@/views/teacher/Classrooms.vue'

vi.mock('@/api/seats', () => ({
  classroomsApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    getSeats: vi.fn(),
  },
  seatsApi: { setBroken: vi.fn() },
  seatOverridesApi: { set: vi.fn(), clear: vi.fn() },
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ showToast: vi.fn(), success: vi.fn(), error: vi.fn() }),
}))

import { classroomsApi } from '@/api/seats'
const mockedList = vi.mocked(classroomsApi.list)
const mockedCreate = vi.mocked(classroomsApi.create)

const twoRooms = () => [
  { id: 1, name: '机房601', rows: 3, cols: 4, status: 'active', seat_count: 12 },
  { id: 2, name: '机房602', rows: 2, cols: 2, status: 'archived', seat_count: 4 },
]

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
  template:
    '<input :value="modelValue" :type="type || \'text\'" :placeholder="placeholder" class="mock-input" @input="$emit(\'update:modelValue\', $event.target.value)" />',
}

const mountComponent = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return mount(Classrooms, {
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

describe('Classrooms 教室管理', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedList.mockResolvedValue(twoRooms())
  })

  it('渲染教室列表：名称 + 布局（rows×cols）+ N 个座位', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('机房601')
    expect(wrapper.text()).toContain('机房602')
    expect(wrapper.text()).toContain('3×4')
    expect(wrapper.text()).toContain('2×2')
    expect(wrapper.text()).toContain('12 个座位')
    expect(wrapper.text()).toContain('4 个座位')
  })

  it('点「新建教室」打开 Dialog，填名称/排/列后创建', async () => {
    mockedCreate.mockResolvedValue({
      id: 3, name: '机房303', rows: 3, cols: 4, status: 'active', seat_count: 12,
    })
    const wrapper = mountComponent()
    await flushPromises()

    const createButton = wrapper.findAll('button').find((b) => b.text().includes('新建教室'))
    expect(createButton).toBeTruthy()
    await createButton!.trigger('click')
    await flushPromises()

    expect(wrapper.find('.mock-dialog').exists()).toBe(true)
    expect(wrapper.text()).toContain('新建教室')

    const inputs = wrapper.findAll('.mock-dialog .mock-input')
    expect(inputs).toHaveLength(3)
    await inputs[0].setValue('机房303')
    await inputs[1].setValue(3)
    await inputs[2].setValue(4)

    const confirmButton = wrapper
      .findAll('.mock-dialog button')
      .find((b) => b.text().trim() === '创建')
    expect(confirmButton).toBeTruthy()
    await confirmButton!.trigger('click')
    await flushPromises()

    expect(mockedCreate).toHaveBeenCalledWith({ name: '机房303', rows: 3, cols: 4 })
  })

  it('seat_count 展示为「N 个座位」', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toMatch(/12\s*个座位/)
  })
})
