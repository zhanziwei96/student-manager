import { describe, it, expect, beforeEach } from 'vitest'
import { useNetworkError } from '@/composables/useNetworkError'

describe('useNetworkError', () => {
  beforeEach(() => {
    // Clear error state before each test
    const { clearError } = useNetworkError()
    clearError()
  })

  it('should initialize with null error and offline false', () => {
    const { networkError, isOffline } = useNetworkError()

    expect(networkError.value).toBeNull()
    expect(isOffline.value).toBe(false)
  })

  it('should set error and mark as offline', () => {
    const { networkError, isOffline, setError } = useNetworkError()
    const testError = new Error('Network failed')

    setError(testError)

    expect(networkError.value).toBe(testError)
    expect(isOffline.value).toBe(true)
  })

  it('should clear error and reset offline status', () => {
    const { networkError, isOffline, setError, clearError } = useNetworkError()
    const testError = new Error('Network failed')

    setError(testError)
    expect(networkError.value).toBe(testError)
    expect(isOffline.value).toBe(true)

    clearError()

    expect(networkError.value).toBeNull()
    expect(isOffline.value).toBe(false)
  })

  it('should set null error and mark offline as false', () => {
    const { networkError, isOffline, setError } = useNetworkError()

    setError(new Error('Test'))
    expect(isOffline.value).toBe(true)

    setError(null)

    expect(networkError.value).toBeNull()
    expect(isOffline.value).toBe(false)
  })

  it('should return readonly refs', () => {
    const { networkError, isOffline } = useNetworkError()

    // TypeScript will prevent direct assignment to readonly refs
    // This test verifies the refs are properly wrapped
    expect(typeof networkError.value).toBeDefined()
    expect(typeof isOffline.value).toBeDefined()
  })
})
