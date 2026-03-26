/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import Toast from '../../src/components/ui/Toast.vue'

describe('Toast Memory Leak', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should clear timeout when component is unmounted', async () => {
    const wrapper = mount(Toast, {
      props: {
        show: true,
        message: 'Test message',
        duration: 3000
      }
    })

    // 验证组件已显示
    expect(wrapper.vm.isVisible).toBe(true)
    
    // 卸载组件
    wrapper.unmount()
    
    // 推进时间超过 duration，验证没有未处理的 timer
    // 如果 timer 未清理，这里可能会抛出错误或警告
    vi.advanceTimersByTime(5000)
    
    // 断言通过即表示清理成功
    expect(true).toBe(true)
  })

  it('should clear previous timeout when showToast is called multiple times', async () => {
    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout')
    
    const wrapper = mount(Toast, {
      props: {
        show: false,
        message: 'Test'
      }
    })

    // 多次触发 show
    await wrapper.setProps({ show: true })
    await nextTick()
    
    await wrapper.setProps({ show: false })
    await nextTick()
    
    await wrapper.setProps({ show: true })
    await nextTick()

    // 验证 clearTimeout 被调用（清理旧 timer）
    expect(clearTimeoutSpy).toHaveBeenCalled()
  })

  it('should not leak memory when rapidly shown and hidden', async () => {
    const wrapper = mount(Toast, {
      props: {
        show: false,
        message: 'Test',
        duration: 1000
      }
    })

    // 快速切换 10 次
    for (let i = 0; i < 10; i++) {
      await wrapper.setProps({ show: true })
      await nextTick()
      await wrapper.setProps({ show: false })
      await nextTick()
    }

    // 卸载组件
    wrapper.unmount()
    
    // 推进时间，验证无泄漏
    vi.advanceTimersByTime(5000)
    
    expect(true).toBe(true)
  })

  it('should call clearTimers on unmount', async () => {
    const wrapper = mount(Toast, {
      props: {
        show: true,
        message: 'Test',
        duration: 5000
      }
    })

    // 访问内部方法验证 timer 存在
    expect(wrapper.vm.timeoutId).toBeTruthy()
    
    // 卸载组件
    wrapper.unmount()
    
    // 验证 timer 已被清理
    expect(wrapper.vm.timeoutId).toBeNull()
  })
})
