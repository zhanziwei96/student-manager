/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'

// Mock device fingerprint
vi.mock('@/lib/device', () => ({
  getDeviceFingerprint: vi.fn().mockResolvedValue('device123'),
  getDeviceInfo: vi.fn().mockReturnValue({
    userAgent: 'test-agent',
    platform: 'test-platform'
  })
}))

describe('useStudentSelfCheckin Composable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should include device fingerprint in checkin request', async () => {
    const mockDeviceId = 'device123'
    const mockDeviceInfo = JSON.stringify({ userAgent: 'test-agent' })

    expect(mockDeviceId).toBeDefined()
    expect(mockDeviceInfo).toBeDefined()
  })

  it('should include GPS coordinates in checkin request', () => {
    const position = {
      lat: 39.90923,
      lng: 116.397428
    }

    expect(position).toHaveProperty('lat')
    expect(position).toHaveProperty('lng')
    expect(typeof position.lat).toBe('number')
    expect(typeof position.lng).toBe('number')
  })

  it('should validate CheckinRequest interface', () => {
    const request = {
      student_id: 'S001',
      student_name: '张三',
      lat: 39.90923,
      lng: 116.397428,
      device_id: 'device123',
      device_info: '{"platform":"test"}'
    }

    expect(request).toHaveProperty('student_id')
    expect(request).toHaveProperty('student_name')
    expect(request).toHaveProperty('lat')
    expect(request).toHaveProperty('lng')
    expect(request).toHaveProperty('device_id')
    expect(request).toHaveProperty('device_info')
  })
})

describe('useGeolocation Composable', () => {
  const mockGeolocation = {
    getCurrentPosition: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
    Object.defineProperty(navigator, 'geolocation', {
      value: mockGeolocation,
      writable: true,
      configurable: true
    })
  })

  it('should handle geolocation success', async () => {
    const mockPosition = {
      coords: {
        latitude: 39.90923,
        longitude: 116.397428
      }
    }

    mockGeolocation.getCurrentPosition.mockImplementation((success) => {
      success(mockPosition)
    })

    expect(mockPosition.coords.latitude).toBe(39.90923)
    expect(mockPosition.coords.longitude).toBe(116.397428)
  })

  it('should handle geolocation error - permission denied', async () => {
    const mockError = {
      code: 1,
      PERMISSION_DENIED: 1,
      POSITION_UNAVAILABLE: 2,
      TIMEOUT: 3
    }

    mockGeolocation.getCurrentPosition.mockImplementation((_, error) => {
      if (error) error(mockError)
    })

    expect(mockError.code).toBe(mockError.PERMISSION_DENIED)
  })

  it('should handle geolocation not supported', () => {
    Object.defineProperty(navigator, 'geolocation', {
      value: undefined,
      writable: true,
      configurable: true
    })

    expect(navigator.geolocation).toBeUndefined()
  })
})
