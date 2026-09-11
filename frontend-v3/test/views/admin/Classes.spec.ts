/**
 * @vitest-environment jsdom
 *
 * 管理员班级管理页 - 创建班级弹窗（专业必填 + 批量创建）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises, type DOMWrapper } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Classes from '@/views/admin/Classes.vue'

const holder = vi.hoisted(() => ({
  showToast: vi.fn(),
  batchCreate: vi.fn(),
  cohortList: vi.fn(),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ showToast: holder.showToast }),
}))

vi.mock('@/api/classes', () => ({
  classesApi: {
    list: vi.fn(() => Promise.resolve([])),
    create: vi.fn(),
    batchCreate: holder.batchCreate,
    update: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('@/api/cohorts', () => ({
  cohortsApi: {
    list: holder.cohortList,
  },
}))

// Mock Dialog 避免 Teleport 问题
const MockDialog = {
  name: 'Dialog',
  props: ['open', 'title', 'description'],
  emits: ['update:open'],
  template: `
    <div v-if="open" class="mock-dialog">
      <h3>{{ title }}</h3>
      <slot />
      <slot name="footer" />
    </div>
  `,
}

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  return mount(Classes, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Dialog: MockDialog,
        Card: { template: '<div><slot /></div>' },
        Badge: { template: '<span><slot /></span>' },
      },
    },
  })
}

/** 打开创建班级弹窗 */
const openDialog = async (wrapper: ReturnType<typeof createWrapper>) => {
  const btn = wrapper.findAll('button').find((b) => b.text().includes('创建班级'))
  await btn!.trigger('click')
  await flushPromises()
  return wrapper.find('.mock-dialog')
}

/** 在弹窗内填写表单：届 / 专业 / 班级名（输入框顺序：专业、班级名） */
const fillForm = async (
  dialog: DOMWrapper<Element>,
  { cohort, major, name }: { cohort?: string; major?: string; name?: string }
) => {
  if (cohort) await dialog.find('select').setValue(cohort)
  const inputs = dialog.findAll('input')
  if (major !== undefined) await inputs[0].setValue(major)
  if (name !== undefined) await inputs[1].setValue(name)
  await flushPromises()
}

/** 点击弹窗内的"创建"按钮 */
const clickCreate = async (dialog: DOMWrapper<Element>) => {
  const btn = dialog.findAll('button').find((b) => b.text().includes('创建'))
  await btn!.trigger('click')
  await flushPromises()
}

describe('Admin Classes - 创建班级弹窗', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    holder.cohortList.mockResolvedValue([{ year: '2026', label: '2026届', status: 'active' }])
    holder.batchCreate.mockResolvedValue({ created_count: 3, created: [], skipped: [] })
  })

  it('专业为空时提示"请输入专业"且不调用接口', async () => {
    const wrapper = createWrapper()
    const dialog = await openDialog(wrapper)

    await fillForm(dialog, { cohort: '2026', name: '1-3' })
    await clickCreate(dialog)

    expect(dialog.text()).toContain('请输入专业')
    expect(holder.batchCreate).not.toHaveBeenCalled()
  })

  it('输入范围写法 1-3 时批量创建，names 展开为三个班级', async () => {
    const wrapper = createWrapper()
    const dialog = await openDialog(wrapper)

    await fillForm(dialog, { cohort: '2026', major: '计算机科学与技术', name: '1-3' })
    await clickCreate(dialog)

    expect(holder.batchCreate).toHaveBeenCalledWith({
      cohort_year: '2026',
      major: '计算机科学与技术',
      names: ['1班', '2班', '3班'],
    })
    expect(holder.showToast).toHaveBeenCalledWith('已创建 3 个班级', 'success')
    // 成功后弹窗关闭
    expect(wrapper.find('.mock-dialog').exists()).toBe(false)
  })

  it('存在跳过项时提示中追加跳过数量', async () => {
    holder.batchCreate.mockResolvedValue({ created_count: 1, created: [], skipped: ['2班'] })
    const wrapper = createWrapper()
    const dialog = await openDialog(wrapper)

    await fillForm(dialog, { cohort: '2026', major: '计算机科学与技术', name: '1-3' })
    await clickCreate(dialog)

    expect(holder.showToast).toHaveBeenCalledWith('已创建 1 个班级，跳过 1 个已存在', 'success')
  })

  it('班级名预览展示完整班级名，超过 5 个时折叠', async () => {
    const wrapper = createWrapper()
    const dialog = await openDialog(wrapper)

    // 未输入班级名时不显示预览
    expect(dialog.text()).not.toContain('将创建')

    await fillForm(dialog, { cohort: '2026', major: '计算机科学与技术', name: '1-3' })
    expect(dialog.text()).toContain(
      '将创建：2026届计算机科学与技术1班、2026届计算机科学与技术2班、2026届计算机科学与技术3班'
    )

    await fillForm(dialog, { name: '1-6' })
    expect(dialog.text()).toContain('将创建：2026届计算机科学与技术1班、2026届计算机科学与技术2班、2026届计算机科学与技术3班、2026届计算机科学与技术4班、2026届计算机科学与技术5班 等 6 个')
  })

  it('届或专业未填时预览只展示班级名（不出现残缺的完整名）', async () => {
    const wrapper = createWrapper()
    const dialog = await openDialog(wrapper)

    // 只填班级名：预览展示解析结果，不含 "届"
    await fillForm(dialog, { name: '1-3' })
    expect(dialog.text()).toContain('将创建：1班、2班、3班')
    expect(dialog.text()).not.toContain('届1班')

    // 只补届、缺专业：仍不拼完整名
    await fillForm(dialog, { cohort: '2026' })
    expect(dialog.text()).toContain('将创建：1班、2班、3班')

    // 补齐专业后才显示完整班级名
    await fillForm(dialog, { major: '软件工程' })
    expect(dialog.text()).toContain('将创建：2026届软件工程1班、2026届软件工程2班、2026届软件工程3班')
  })
})
