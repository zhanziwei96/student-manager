/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import StudentImportDialog from '../../src/components/admin/StudentImportDialog.vue'

// --- Mocks ---

const downloadTemplateMock = vi.fn()
const importMock = vi.fn()
vi.mock('@/api/students', () => ({
  studentsApi: {
    downloadImportTemplate: (...args: unknown[]) => downloadTemplateMock(...args),
    import: (...args: unknown[]) => importMock(...args),
  },
}))

const successToast = vi.fn()
const errorToast = vi.fn()
const warningToast = vi.fn()
vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    showToast: (msg: string, type?: string) => {
      if (type === 'error') errorToast(msg, type)
      else if (type === 'warning') warningToast(msg, type)
      else successToast(msg, type)
    },
  }),
}))

vi.mock('@/lib/error', () => ({
  getErrorMessage: (err: unknown) => (err instanceof Error ? err.message : ''),
}))

vi.mock('@vueuse/core', () => ({
  useScrollLock: () => ({ value: false }),
}))

// --- Helpers ---

const mountDialog = () =>
  mount(StudentImportDialog, {
    props: { open: true },
    global: { stubs: { teleport: true } },
  })

const selectFile = async (wrapper: ReturnType<typeof mountDialog>, file = new File(['x'], 'students.xlsx')) => {
  const input = wrapper.find('[data-testid="import-file"]')
  Object.defineProperty(input.element, 'files', { value: [file], configurable: true })
  await input.trigger('change')
}

describe('StudentImportDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // 模板下载走 URL.createObjectURL，jsdom 未实现
    window.URL.createObjectURL = vi.fn(() => 'blob:mock')
    window.URL.revokeObjectURL = vi.fn()
  })

  it('展示导入说明与模板下载入口', () => {
    const wrapper = mountDialog()

    expect(wrapper.text()).toContain('学号、姓名、所属届、班级名')
    expect(wrapper.find('[data-testid="download-template"]').exists()).toBe(true)
  })

  it('点击下载模板调用 API', async () => {
    downloadTemplateMock.mockResolvedValue(new Blob(['x']))
    const wrapper = mountDialog()

    await wrapper.find('[data-testid="download-template"]').trigger('click')
    await flushPromises()

    expect(downloadTemplateMock).toHaveBeenCalledTimes(1)
  })

  it('未选择文件时导入按钮禁用', () => {
    const wrapper = mountDialog()
    expect(wrapper.find('[data-testid="submit-import"]').attributes('disabled')).toBeDefined()
  })

  it('导入成功后展示结果并通知父组件刷新', async () => {
    importMock.mockResolvedValue({
      imported: 2,
      skipped: 1,
      skipped_rows: ['第 3 行: 学号 S001 已存在，已跳过'],
      errors: [],
    })
    const wrapper = mountDialog()
    await selectFile(wrapper)

    await wrapper.find('[data-testid="submit-import"]').trigger('click')
    await flushPromises()

    expect(importMock).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('成功 2')
    expect(wrapper.text()).toContain('跳过 1')
    expect(wrapper.text()).toContain('S001 已存在')
    expect(wrapper.emitted('imported')).toBeTruthy()
    expect(successToast).toHaveBeenCalledWith('成功导入 2 名学生', 'success')
  })

  it('导入失败行会展示错误清单且不通知刷新', async () => {
    importMock.mockResolvedValue({
      imported: 0,
      skipped: 0,
      skipped_rows: [],
      errors: ['第 2 行: 班级 \'X班\' 不存在且未填写所属届'],
    })
    const wrapper = mountDialog()
    await selectFile(wrapper)

    await wrapper.find('[data-testid="submit-import"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('失败 1')
    expect(wrapper.text()).toContain('不存在且未填写所属届')
    expect(wrapper.emitted('imported')).toBeFalsy()
    expect(warningToast).toHaveBeenCalled()
  })

  it('导入抛错时提示错误', async () => {
    importMock.mockRejectedValue(new Error('缺少必需列: 姓名'))
    const wrapper = mountDialog()
    await selectFile(wrapper)

    await wrapper.find('[data-testid="submit-import"]').trigger('click')
    await flushPromises()

    expect(errorToast).toHaveBeenCalledWith('缺少必需列: 姓名', 'error')
  })
})
