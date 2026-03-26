import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useToast } from '@/composables/useToast'

/**
 * useToast composable 测试
 * REVIEW-P1: 验证全局 Toast 功能
 */
describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should initialize with default values', () => {
    const { show, message, variant } = useToast()

    expect(show.value).toBe(false)
    expect(message.value).toBe('')
    expect(variant.value).toBe('default')
  })

  it('should show toast with options object', () => {
    const { show, message, variant, showToast } = useToast()

    showToast({ message: 'Test message', variant: 'success' })

    expect(show.value).toBe(true)
    expect(message.value).toBe('Test message')
    expect(variant.value).toBe('success')
  })

  it('should support convenient string call signature', () => {
    const { show, message, variant, showToast } = useToast()

    // 便捷调用: showToast('message', 'variant')
    showToast('Quick message', 'error')

    expect(show.value).toBe(true)
    expect(message.value).toBe('Quick message')
    expect(variant.value).toBe('error')
  })

  it('should support convenient call with duration', () => {
    const { show, message, variant, showToast } = useToast()

    // 便捷调用: showToast('message', 'variant', duration)
    showToast('With duration', 'warning', 5000)

    expect(show.value).toBe(true)
    expect(message.value).toBe('With duration')
    expect(variant.value).toBe('warning')
  })

  it('should hide toast', () => {
    const { show, showToast, hideToast } = useToast()

    showToast({ message: 'Test' })
    expect(show.value).toBe(true)

    hideToast()
    expect(show.value).toBe(false)
  })

  it('should provide success shortcut method', () => {
    const { show, message, variant, success } = useToast()

    success('Success!')

    expect(show.value).toBe(true)
    expect(message.value).toBe('Success!')
    expect(variant.value).toBe('success')
  })

  it('should provide error shortcut method', () => {
    const { show, message, variant, error } = useToast()

    error('Error!')

    expect(show.value).toBe(true)
    expect(message.value).toBe('Error!')
    expect(variant.value).toBe('error')
  })

  it('should provide warning shortcut method', () => {
    const { show, message, variant, warning } = useToast()

    warning('Warning!')

    expect(show.value).toBe(true)
    expect(message.value).toBe('Warning!')
    expect(variant.value).toBe('warning')
  })

  it('should provide info shortcut method', () => {
    const { show, message, variant, info } = useToast()

    info('Info!')

    expect(show.value).toBe(true)
    expect(message.value).toBe('Info!')
    expect(variant.value).toBe('info')
  })

  it('should use default variant when not specified', () => {
    const { variant, showToast } = useToast()

    showToast({ message: 'No variant' })

    expect(variant.value).toBe('default')
  })

  it('should use default duration when not specified', () => {
    const { duration, showToast } = useToast()

    showToast({ message: 'No duration' })

    expect(duration.value).toBe(3000)
  })

  it('should allow custom duration', () => {
    const { duration, showToast } = useToast()

    showToast({ message: 'Custom duration', duration: 5000 })

    expect(duration.value).toBe(5000)
  })

  it('should allow custom duration in shortcut methods', () => {
    const { duration, success } = useToast()

    success('Quick', 1000)

    expect(duration.value).toBe(1000)
  })
})
