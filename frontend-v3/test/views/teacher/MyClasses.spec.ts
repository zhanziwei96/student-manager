/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import MyClasses from '@/views/teacher/MyClasses.vue'
import { teacherClassesApi } from '@/api/teacherClasses'

vi.mock('@/api/teacherClasses', () => ({
  teacherClassesApi: {
    getMine: vi.fn(),
    updateMine: vi.fn(),
    getAll: vi.fn(),
  },
}))

vi.mock('@/composables', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

const stubs = {
  Card: { template: '<div class="card"><slot /></div>' },
  Button: {
    props: ['loading', 'disabled'],
    template: '<button class="btn" :disabled="disabled"><slot /></button>',
  },
  Checkbox: {
    props: ['checked'],
    emits: ['update:checked'],
    template: '<input type="checkbox" class="checkbox" :checked="checked" @change="$emit(\'update:checked\', $event.target.checked)" />',
  },
  DataContainer: {
    props: ['loading', 'error', 'hasData'],
    template: '<div class="data-container"><slot /></div>',
  },
}

function createTestQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function mountMyClasses() {
  const queryClient = createTestQueryClient()
  return mount(MyClasses, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs,
    },
  })
}

describe('MyClasses', () => {
  beforeEach(() => {
    vi.mocked(teacherClassesApi.getMine).mockResolvedValue(['计算机1班'])
    vi.mocked(teacherClassesApi.getAll).mockResolvedValue([
      { name: '计算机1班', status: 'active' },
      { name: '计算机2班', status: 'active' },
    ])
    vi.mocked(teacherClassesApi.updateMine).mockResolvedValue(undefined)
  })

  it('displays current classes with the correct checked state', async () => {
    const wrapper = mountMyClasses()
    await flushPromises()
    await nextTick()

    expect(wrapper.text()).toContain('我的班级')
    expect(wrapper.text()).toContain('计算机1班')
    expect(wrapper.text()).toContain('计算机2班')

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    expect(checkboxes).toHaveLength(2)
    expect((checkboxes[0].element as HTMLInputElement).checked).toBe(true)
    expect((checkboxes[1].element as HTMLInputElement).checked).toBe(false)
  })

  it('saves the updated class list when adding a class', async () => {
    const wrapper = mountMyClasses()
    await flushPromises()
    await nextTick()

    // 勾选计算机2班
    await wrapper.findAll('input[type="checkbox"]')[1].setValue(true)
    await nextTick()

    const saveBtn = wrapper.findAll('button').find((b) => b.text().includes('保存'))
    expect(saveBtn).toBeTruthy()
    await saveBtn!.trigger('click')
    await flushPromises()

    expect(teacherClassesApi.updateMine).toHaveBeenCalledWith(['计算机1班', '计算机2班'])
  })

  it('saves an empty list when unchecking all classes', async () => {
    const wrapper = mountMyClasses()
    await flushPromises()
    await nextTick()

    // 取消勾选计算机1班
    await wrapper.findAll('input[type="checkbox"]')[0].setValue(false)
    await nextTick()

    const saveBtn = wrapper.findAll('button').find((b) => b.text().includes('保存'))
    await saveBtn!.trigger('click')
    await flushPromises()

    expect(teacherClassesApi.updateMine).toHaveBeenCalledWith([])
  })
})
