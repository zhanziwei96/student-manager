/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ResponsiveDialog from '@/components/ui/ResponsiveDialog.vue'

// BottomSheet 内部使用 useRoute 监听路由切换关闭
vi.mock('vue-router', () => ({
  useRoute: () => ({ path: '/' })
}))

const originalInnerWidth = window.innerWidth

const setViewport = (width: number) => {
  Object.defineProperty(window, 'innerWidth', {
    value: width,
    writable: true,
    configurable: true,
  })
}

const mountDialog = () =>
  mount(ResponsiveDialog, {
    props: { open: true, title: '测试标题', description: '测试描述' },
    slots: {
      default: '<p class="body-content">正文内容</p>',
      footer: '<button class="footer-action">确认</button>',
    },
    attachTo: document.body,
  })

describe('ResponsiveDialog', () => {
  afterEach(() => {
    setViewport(originalInnerWidth)
    document.body.innerHTML = ''
    document.body.style.overflow = ''
  })

  it('桌面端（≥768px）渲染居中 Dialog', async () => {
    setViewport(1024)
    const wrapper = mountDialog()
    await flushPromises()

    // Dialog 居中容器；无 BottomSheet 的拖拽手柄 / role=dialog
    expect(document.body.querySelector('.max-w-lg')).toBeTruthy()
    expect(document.body.querySelector('.touch-none')).toBeNull()
    expect(document.body.querySelector('[role="dialog"]')).toBeNull()

    wrapper.unmount()
  })

  it('移动端（<768px）渲染 BottomSheet', async () => {
    setViewport(375)
    const wrapper = mountDialog()
    await flushPromises()

    // BottomSheet：role=dialog + 顶部拖拽手柄；无桌面 Dialog 容器
    const sheet = document.body.querySelector('[role="dialog"]')
    expect(sheet).toBeTruthy()
    expect(sheet!.className).toContain('rounded-t-sheet')
    expect(document.body.querySelector('.touch-none')).toBeTruthy()
    expect(document.body.querySelector('.max-w-lg')).toBeNull()

    wrapper.unmount()
  })

  it('桌面端渲染标题、描述、正文与 footer 插槽', async () => {
    setViewport(1024)
    const wrapper = mountDialog()
    await flushPromises()

    expect(document.body.textContent).toContain('测试标题')
    expect(document.body.textContent).toContain('测试描述')
    expect(document.body.querySelector('.body-content')).toBeTruthy()
    expect(document.body.querySelector('.footer-action')).toBeTruthy()

    wrapper.unmount()
  })

  it('移动端渲染标题、描述、正文与 footer 插槽', async () => {
    setViewport(375)
    const wrapper = mountDialog()
    await flushPromises()

    const sheet = document.body.querySelector('[role="dialog"]')
    expect(sheet).toBeTruthy()
    expect(sheet!.textContent).toContain('测试标题')
    expect(sheet!.textContent).toContain('测试描述')
    expect(sheet!.querySelector('.body-content')).toBeTruthy()
    expect(sheet!.querySelector('.footer-action')).toBeTruthy()

    wrapper.unmount()
  })

  it('移动端遮罩点击关闭时触发 update:open', async () => {
    setViewport(375)
    const wrapper = mountDialog()
    await flushPromises()

    const overlay = document.body.querySelector('.fixed.inset-0.z-50')
    expect(overlay).toBeTruthy()
    overlay!.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()

    expect(wrapper.emitted('update:open')).toBeTruthy()
    expect(wrapper.emitted('update:open')![0]).toEqual([false])

    wrapper.unmount()
  })
})
