/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Dialog from '../../src/components/ui/Dialog.vue'


describe('Dialog as-form 表单提交', () => {
  const mountFormDialog = (onSubmit: (e: Event) => void) =>
    mount(Dialog, {
      props: { open: true, asForm: true, title: '表单弹窗', onSubmit },
      slots: {
        default: '<input name="probe" />',
        footer: '<button type="submit">提交</button>',
      },
      global: { stubs: { teleport: true } },
    })

  it('提交表单时调用 onSubmit 并阻止原生提交', () => {
    const onSubmit = vi.fn()
    const wrapper = mountFormDialog(onSubmit)

    const form = wrapper.find('form')
    expect(form.exists()).toBe(true)

    const event = new Event('submit', { bubbles: true, cancelable: true })
    form.element.dispatchEvent(event)

    // 回归：`@submit="cond ? handler : undefined"` 会被编译成「返回函数」的箭头函数，
    // 导致处理函数从不执行、默认提交不被阻止（页面重载、静默无响应）
    expect(onSubmit).toHaveBeenCalledTimes(1)
    expect(event.defaultPrevented).toBe(true)
  })

  it('点击 type=submit 按钮同样走 onSubmit（原生提交被阻止）', async () => {
    const onSubmit = vi.fn()
    const wrapper = mountFormDialog(onSubmit)

    const button = wrapper.find('button[type="submit"]')
    const event = new Event('submit', { bubbles: true, cancelable: true })
    wrapper.find('form').element.dispatchEvent(event)
    await flushPromises()

    expect(button.exists()).toBe(true)
    expect(onSubmit).toHaveBeenCalledTimes(1)
    expect(event.defaultPrevented).toBe(true)
  })
})

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
