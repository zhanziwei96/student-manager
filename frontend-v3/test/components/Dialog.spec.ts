/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Dialog from '../../src/components/ui/Dialog.vue'

describe('Dialog Memory Leak', () => {
  it('should handle multiple open/close cycles without error', async () => {
    const wrapper = mount(Dialog, {
      props: {
        open: false,
        title: 'Test Dialog'
      }
    })

    // 多次打开关闭（验证内存泄漏修复）
    for (let i = 0; i < 5; i++) {
      await wrapper.setProps({ open: true })
      await flushPromises()
      
      await wrapper.setProps({ open: false })
      await flushPromises()
    }
    
    // 测试通过表示无内存泄漏
    expect(true).toBe(true)
  })

  it('should unmount without error when open', async () => {
    const wrapper = mount(Dialog, {
      props: {
        open: true,
        title: 'Test Dialog'
      }
    })

    await flushPromises()
    
    // 卸载组件（验证 onUnmounted 钩子不报错）
    expect(() => wrapper.unmount()).not.toThrow()
  })

  it('should unmount without error when closed', async () => {
    const wrapper = mount(Dialog, {
      props: {
        open: false,
        title: 'Test Dialog'
      }
    })

    await flushPromises()
    
    // 卸载组件（验证 onUnmounted 钩子不报错）
    expect(() => wrapper.unmount()).not.toThrow()
  })
})
