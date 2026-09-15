/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { useSwipeBack } from '@/composables/useSwipeBack'

/**
 * useSwipeBack composable 测试
 * 验证左缘起手、水平主导判定与 router.back 调用
 */

const { back } = vi.hoisted(() => ({ back: vi.fn() }))
vi.mock('vue-router', () => ({ useRouter: () => ({ back }) }))

// jsdom 不支持 TouchEvent 构造器，用 Event + 补丁模拟触摸事件
function makeTouchEvent(type: string, x: number, y: number): TouchEvent {
  const touch = { clientX: x, clientY: y, identifier: 0 }
  return Object.assign(new Event(type, { bubbles: true, cancelable: true }), {
    touches: type === 'touchend' ? [] : [touch],
    changedTouches: [touch],
  }) as unknown as TouchEvent
}

function setup() {
  const wrapper = mount(
    defineComponent({
      setup() {
        useSwipeBack()
        return () => h('div')
      },
    }),
  )
  return { unmount: () => wrapper.unmount() }
}

describe('useSwipeBack', () => {
  const cleanups: Array<() => void> = []

  afterEach(() => {
    cleanups.splice(0).forEach((fn) => fn())
    back.mockClear()
  })

  it('左缘内起手且水平右滑达阈值时调用 router.back', () => {
    const { unmount } = setup()
    cleanups.push(unmount)

    window.dispatchEvent(makeTouchEvent('touchstart', 10, 200))
    window.dispatchEvent(makeTouchEvent('touchend', 160, 200))
    expect(back).toHaveBeenCalledTimes(1)
  })

  it('屏幕中部起手时不触发返回', () => {
    const { unmount } = setup()
    cleanups.push(unmount)

    window.dispatchEvent(makeTouchEvent('touchstart', 200, 200))
    window.dispatchEvent(makeTouchEvent('touchend', 400, 200))
    expect(back).not.toHaveBeenCalled()
  })

  it('垂直主导的手势不触发返回', () => {
    const { unmount } = setup()
    cleanups.push(unmount)

    // deltaX = 120 达阈值，但 deltaY = 70，120 <= 70 * 2
    window.dispatchEvent(makeTouchEvent('touchstart', 10, 100))
    window.dispatchEvent(makeTouchEvent('touchend', 130, 170))
    expect(back).not.toHaveBeenCalled()
  })

  it('水平位移未达阈值时不触发返回', () => {
    const { unmount } = setup()
    cleanups.push(unmount)

    window.dispatchEvent(makeTouchEvent('touchstart', 10, 200))
    window.dispatchEvent(makeTouchEvent('touchend', 80, 200))
    expect(back).not.toHaveBeenCalled()
  })

  it('卸载后移除监听，不再响应触摸', () => {
    const { unmount } = setup()
    unmount()

    window.dispatchEvent(makeTouchEvent('touchstart', 10, 200))
    window.dispatchEvent(makeTouchEvent('touchend', 160, 200))
    expect(back).not.toHaveBeenCalled()
  })
})
