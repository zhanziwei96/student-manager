/**
 * 签到API测试
 */
import { describe, it, expect } from 'vitest'
import type { CheckinRequest, CourseSessionStatus } from '@/types'

describe('Checkin API Types', () => {
  it('should validate CheckinRequest with GPS and device info', () => {
    const request: CheckinRequest = {
      student_id: 'S001',
      student_name: '张三',
      lat: 39.90923,
      lng: 116.397428,
      device_id: 'device123',
      device_info: '{"platform":"test"}'
    }

    expect(request.student_id).toBe('S001')
    expect(request.lat).toBe(39.90923)
    expect(request.lng).toBe(116.397428)
    expect(request.device_id).toBe('device123')
  })

  it('should validate CourseSessionStatus with location', () => {
    const status: CourseSessionStatus = {
      active: true,
      location_name: '机房312',
      checkin_radius: 100,
      require_location: true
    }

    expect(status.location_name).toBe('机房312')
    expect(status.checkin_radius).toBe(100)
  })
})
