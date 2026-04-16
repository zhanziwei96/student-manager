/**
 * 设备指纹工具测试 - FingerprintJS 版本
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { getEnhancedDeviceFingerprint, getDeviceInfo, clearDeviceId } from '@/lib/device'

// Mock FingerprintJS
// 注意：vi.mock 工厂函数会被提升到顶部，不能引用外部变量
vi.mock('@fingerprintjs/fingerprintjs', () => ({
  default: {
    load: vi.fn().mockResolvedValue({
      get: vi.fn().mockResolvedValue({ visitorId: 'mock-fp-visitor-id-12345' }),
    }),
  },
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('Device Fingerprint', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
  })

  it('should generate device fingerprint via FingerprintJS', async () => {
    const fingerprint = await getEnhancedDeviceFingerprint()

    expect(fingerprint).toHaveLength(64)
    expect(localStorageMock.setItem).toHaveBeenCalledWith('checkin_device_id', fingerprint)
  })

  it('should return cached device id if exists', async () => {
    const cachedId = 'cached-device-id'
    localStorageMock.getItem.mockReturnValue(cachedId)

    const fingerprint = await getEnhancedDeviceFingerprint()

    expect(fingerprint).toBe(cachedId)
    expect(localStorageMock.setItem).not.toHaveBeenCalled()
  })

  it('should get device info object', () => {
    const info = getDeviceInfo()

    expect(info).toHaveProperty('userAgent')
    expect(info).toHaveProperty('platform')
    expect(info).toHaveProperty('language')
    expect(info).toHaveProperty('screen')
    expect(info).toHaveProperty('hardwareConcurrency')
    expect(info).toHaveProperty('deviceMemory')
    expect(info).toHaveProperty('maxTouchPoints')
    expect(info).toHaveProperty('timezoneOffset')
  })

  it('should clear device id and salt', () => {
    clearDeviceId()
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('checkin_device_id')
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('checkin_device_salt')
  })
})
