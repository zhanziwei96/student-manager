/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import BottomSheet from '@/components/ui/BottomSheet.vue'

// BottomSheet 内部使用 useRoute 监听路由切换关闭
vi.mock('vue-router', () => ({
  useRoute: () => ({ path: '/' })
}))

/**
 * 构造触摸事件（jsdom 无 TouchEvent 构造器）
 */
const makeTouchEvent = (type: string, clientY: number) => {
  const event = new Event(type, { bubbles: true, cancelable: true })
  Object.defineProperty(event, 'touches', {
    value: clientY < 0 ? [] : [{ clientY }]
  })
  return event
}

/** 在拖拽手柄上模拟一段下滑手势 */
const dragHandle = async (fromY: number, toY: number) => {
  const handle = document.body.querySelector('.touch-none')
  expect(handle).toBeTruthy()
  handle!.dispatchEvent(makeTouchEvent('touchstart', fromY))
  handle!.dispatchEvent(makeTouchEvent('touchmove', toY))
  handle!.dispatchEvent(makeTouchEvent('touchend', -1))
  await flushPromises()
}

describe('BottomSheet', () => {
  beforeEach(() => {
    document.body.style.overflow = ''
    document.body.innerHTML = ''
  })

  afterEach(() => {
    document.body.style.overflow = ''
    document.body.innerHTML = ''
  })

  it('closed by default when open=false', async () => {
    const wrapper = mount(BottomSheet, {
      props: { open: false, title: '隐藏面板' },
      slots: { default: '内容' },
      attachTo: document.body
    })

    await flushPromises()

    expect(document.body.querySelector('[role="dialog"]')).toBeNull()
    expect(document.body.textContent).not.toContain('隐藏面板')

    wrapper.unmount()
  })

  it('renders slot content and title when open=true', async () => {
    const wrapper = mount(BottomSheet, {
      props: { open: true, title: '更多操作' },
      slots: { default: '<p>面板内容</p>' },
      attachTo: document.body
    })

    await flushPromises()

    expect(document.body.querySelector('[role="dialog"]')).toBeTruthy()
    expect(document.body.textContent).toContain('更多操作')
    expect(document.body.textContent).toContain('面板内容')
    // 顶部拖拽手柄
    expect(document.body.querySelector('.touch-none')).toBeTruthy()

    wrapper.unmount()
  })

  it('emits update:open false on backdrop click', async () => {
    const wrapper = mount(BottomSheet, {
      props: { open: true },
      attachTo: document.body
    })

    await flushPromises()

    const backdrop = document.body.querySelector('[class*="bg-black"]')
    expect(backdrop).toBeTruthy()
    backdrop!.dispatchEvent(new MouseEvent('click', { bubbles: true }))

    await flushPromises()

    expect(wrapper.emitted('update:open')).toBeTruthy()
    expect(wrapper.emitted('update:open')![0]).toEqual([false])

    wrapper.unmount()
  })

  it('emits update:open false when dragged past threshold', async () => {
    const wrapper = mount(BottomSheet, {
      props: { open: true },
      attachTo: document.body
    })

    await flushPromises()

    // jsdom 无布局，阈值回退 80px：下滑 200px 触发关闭
    await dragHandle(100, 300)

    expect(wrapper.emitted('update:open')).toBeTruthy()
    expect(wrapper.emitted('update:open')![0]).toEqual([false])

    wrapper.unmount()
  })

  it('springs back without emitting on small drag', async () => {
    const wrapper = mount(BottomSheet, {
      props: { open: true },
      attachTo: document.body
    })

    await flushPromises()

    // 小幅下滑 20px：未过阈值，回弹不关闭
    await dragHandle(100, 120)

    expect(wrapper.emitted('update:open')).toBeFalsy()

    wrapper.unmount()
  })

  it('locks body scroll while open and restores after close', async () => {
    const wrapper = mount(BottomSheet, {
      props: { open: true },
      attachTo: document.body
    })

    await flushPromises()
    expect(document.body.style.overflow).toBe('hidden')

    await wrapper.setProps({ open: false })
    await flushPromises()
    expect(document.body.style.overflow).toBe('')

    wrapper.unmount()
  })
})
