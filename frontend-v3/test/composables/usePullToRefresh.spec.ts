/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { defineComponent, h, ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { usePullToRefresh } from '@/composables/usePullToRefresh'

/**
 * usePullToRefresh composable 测试
 * 验证下拉刷新的阈值触发与顶部约束
 */

// jsdom 不支持 TouchEvent 构造器，用 Event + 补丁模拟触摸事件
function makeTouchEvent(type: string, x: number, y: number): TouchEvent {
  const touch = { clientX: x, clientY: y, identifier: 0 }
  return Object.assign(new Event(type, { bubbles: true, cancelable: true }), {
    touches: type === 'touchend' ? [] : [touch],
    changedTouches: [touch],
  }) as unknown as TouchEvent
}

function setup(onRefresh: () => Promise<unknown> | void, threshold?: number) {
  const container = document.createElement('div')
  document.body.appendChild(container)
  let api!: ReturnType<typeof usePullToRefresh>
  const wrapper = mount(
    defineComponent({
      setup() {
        const containerRef = ref<HTMLElement | null>(container)
        api = usePullToRefresh(containerRef, onRefresh, threshold ? { threshold } : undefined)
        return () => h('div')
      },
    }),
  )
  return {
    container,
    api,
    unmount: () => {
      wrapper.unmount()
      container.remove()
    },
  }
}

describe('usePullToRefresh', () => {
  const cleanups: Array<() => void> = []

  afterEach(() => {
    cleanups.splice(0).forEach((fn) => fn())
  })

  it('下拉超过阈值且位于顶部时触发 onRefresh', async () => {
    const onRefresh = vi.fn().mockResolvedValue(undefined)
    const { container, api, unmount } = setup(onRefresh)
    cleanups.push(unmount)

    container.dispatchEvent(makeTouchEvent('touchstart', 100, 100))
    // raw = 300，经阻力曲线后封顶 120px
    container.dispatchEvent(makeTouchEvent('touchmove', 100, 400))
    expect(api.pulling.value).toBe(true)
    expect(api.pullDistance.value).toBe(120)

    container.dispatchEvent(makeTouchEvent('touchend', 100, 400))
    expect(onRefresh).toHaveBeenCalledTimes(1)

    await flushPromises()
    expect(api.refreshing.value).toBe(false)
    expect(api.pullDistance.value).toBe(0)
  })

  it('下拉未达阈值时不触发 onRefresh 并回弹', () => {
    const onRefresh = vi.fn()
    const { container, api, unmount } = setup(onRefresh)
    cleanups.push(unmount)

    container.dispatchEvent(makeTouchEvent('touchstart', 100, 100))
    // raw = 50 → 20px，低于默认阈值 80
    container.dispatchEvent(makeTouchEvent('touchmove', 100, 150))
    expect(api.pullDistance.value).toBe(20)

    container.dispatchEvent(makeTouchEvent('touchend', 100, 150))
    expect(onRefresh).not.toHaveBeenCalled()
    expect(api.pulling.value).toBe(false)
    expect(api.pullDistance.value).toBe(0)
  })

  it('容器不在顶部（scrollTop > 0）时不响应下拉', () => {
    const onRefresh = vi.fn()
    const { container, api, unmount } = setup(onRefresh)
    cleanups.push(unmount)

    container.scrollTop = 50
    container.dispatchEvent(makeTouchEvent('touchstart', 100, 100))
    container.dispatchEvent(makeTouchEvent('touchmove', 100, 400))
    container.dispatchEvent(makeTouchEvent('touchend', 100, 400))

    expect(onRefresh).not.toHaveBeenCalled()
    expect(api.pulling.value).toBe(false)
    expect(api.pullDistance.value).toBe(0)
  })

  it('卸载后移除监听，不再响应触摸', () => {
    const onRefresh = vi.fn()
    const { container, unmount } = setup(onRefresh)
    unmount()

    container.dispatchEvent(makeTouchEvent('touchstart', 100, 100))
    container.dispatchEvent(makeTouchEvent('touchmove', 100, 400))
    container.dispatchEvent(makeTouchEvent('touchend', 100, 400))
    expect(onRefresh).not.toHaveBeenCalled()
  })
})
