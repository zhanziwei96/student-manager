/**
 * 设备指纹工具测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { getDeviceFingerprint, getDeviceInfo, clearDeviceId } from '@/lib/device'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn()
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

describe('Device Fingerprint', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
  })

  it('should generate device fingerprint', async () => {
    const fingerprint = await getDeviceFingerprint()
    
    // 验证指纹是32位十六进制字符串
    expect(fingerprint).toMatch(/^[a-f0-9]{32}$/)
    // 验证指纹被保存到localStorage
    expect(localStorageMock.setItem).toHaveBeenCalledWith('checkin_device_id', fingerprint)
  })

  it('should return cached device id if exists', async () => {
    const cachedId = 'abc123def456'
    localStorageMock.getItem.mockReturnValue(cachedId)
    
    const fingerprint = await getDeviceFingerprint()
    
    // 验证返回缓存的ID
    expect(fingerprint).toBe(cachedId)
    // 验证没有生成新指纹
    expect(localStorageMock.setItem).not.toHaveBeenCalled()
  })

  it('should return consistent fingerprint for same device', async () => {
    // 生成两次指纹
    const fp1 = await getDeviceFingerprint()
    
    // 清除缓存，模拟重新生成
    localStorageMock.getItem.mockReturnValue(null)
    
    const fp2 = await getDeviceFingerprint()
    
    // 两次生成的指纹应该相同（同一设备特征）
    expect(fp1).toBe(fp2)
  })

  it('should get device info object', () => {
    const info = getDeviceInfo()
    
    // 验证设备信息包含必要字段
    expect(info).toHaveProperty('userAgent')
    expect(info).toHaveProperty('platform')
    expect(info).toHaveProperty('language')
    expect(info).toHaveProperty('screen')
    expect(info).toHaveProperty('hardwareConcurrency')
    expect(info).toHaveProperty('timezoneOffset')
  })

  it('should clear device id', () => {
    clearDeviceId()
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('checkin_device_id')
  })
})
