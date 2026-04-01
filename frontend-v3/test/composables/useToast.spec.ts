import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useToast, toasts } from '@/composables/useToast'

/**
 * useToast composable 测试
 * 验证队列模式 Toast 功能
 */
describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    // 清空 toast 队列
    toasts.value = []
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should initialize with empty queue', () => {
    const { toasts: toastList } = useToast()

    expect(toastList.value).toEqual([])
  })

  it('should show toast with options object', () => {
    const { toasts: toastList, showToast } = useToast()

    showToast({ message: 'Test message', variant: 'success' })

    expect(toastList.value).toHaveLength(1)
    expect(toastList.value[0].message).toBe('Test message')
    expect(toastList.value[0].variant).toBe('success')
  })

  it('should support convenient string call signature', () => {
    const { toasts: toastList, showToast } = useToast()

    // 便捷调用: showToast('message', 'variant')
    showToast('Quick message', 'error')

    expect(toastList.value).toHaveLength(1)
    expect(toastList.value[0].message).toBe('Quick message')
    expect(toastList.value[0].variant).toBe('error')
  })

  it('should support convenient call with duration', () => {
    const { toasts: toastList, showToast } = useToast()

    // 便捷调用: showToast('message', 'variant', duration)
    showToast('With duration', 'warning', 5000)

    expect(toastList.value).toHaveLength(1)
    expect(toastList.value[0].message).toBe('With duration')
    expect(toastList.value[0].variant).toBe('warning')
    expect(toastList.value[0].duration).toBe(5000)
  })

  it('should hide toast by id', () => {
    const { toasts: toastList, showToast, hideToast } = useToast()

    showToast({ message: 'Test' })
    expect(toastList.value).toHaveLength(1)

    const toastId = toastList.value[0].id
    hideToast(toastId)
    expect(toastList.value).toHaveLength(0)
  })

  it('should provide success shortcut method', () => {
    const { toasts: toastList, success } = useToast()

    success('Success!')

    expect(toastList.value).toHaveLength(1)
    expect(toastList.value[0].message).toBe('Success!')
    expect(toastList.value[0].variant).toBe('success')
  })

  it('should provide error shortcut method', () => {
    const { toasts: toastList, error } = useToast()

    error('Error!')

    expect(toastList.value).toHaveLength(1)
    expect(toastList.value[0].message).toBe('Error!')
    expect(toastList.value[0].variant).toBe('error')
  })

  it('should provide warning shortcut method', () => {
    const { toasts: toastList, warning } = useToast()

    warning('Warning!')

    expect(toastList.value).toHaveLength(1)
    expect(toastList.value[0].message).toBe('Warning!')
    expect(toastList.value[0].variant).toBe('warning')
  })

  it('should provide info shortcut method', () => {
    const { toasts: toastList, info } = useToast()

    info('Info!')

    expect(toastList.value).toHaveLength(1)
    expect(toastList.value[0].message).toBe('Info!')
    expect(toastList.value[0].variant).toBe('info')
  })

  it('should use default variant when not specified', () => {
    const { toasts: toastList, showToast } = useToast()

    showToast({ message: 'No variant' })

    expect(toastList.value[0].variant).toBe('default')
  })

  it('should use default duration when not specified', () => {
    const { toasts: toastList, showToast } = useToast()

    showToast({ message: 'No duration' })

    expect(toastList.value[0].duration).toBe(3000)
  })

  it('should allow custom duration', () => {
    const { toasts: toastList, showToast } = useToast()

    showToast({ message: 'Custom duration', duration: 5000 })

    expect(toastList.value[0].duration).toBe(5000)
  })

  it('should allow custom duration in shortcut methods', () => {
    const { toasts: toastList, success } = useToast()

    success('Quick', 1000)

    expect(toastList.value[0].duration).toBe(1000)
  })

  it('should support multiple toasts in queue', () => {
    const { toasts: toastList, success, error, info } = useToast()

    success('First')
    error('Second')
    info('Third')

    expect(toastList.value).toHaveLength(3)
    expect(toastList.value[0].message).toBe('First')
    expect(toastList.value[1].message).toBe('Second')
    expect(toastList.value[2].message).toBe('Third')
  })
})
