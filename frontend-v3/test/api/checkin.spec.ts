/**
 * 签到API类型测试
 */
import { describe, it, expect } from 'vitest'
import type { CheckinRequest, CourseSessionStatus } from '@/types'

describe('Checkin API Types', () => {
  it('should validate CheckinRequest with verification code and device info', () => {
    const request: CheckinRequest = {
      student_id: 'S001',
      student_name: '张三',
      verification_code: 'ABC123',
      device_id: 'device123',
      device_info: '{"platform":"test"}'
    }

    expect(request.student_id).toBe('S001')
    expect(request.student_name).toBe('张三')
    expect(request.verification_code).toBe('ABC123')
    expect(request.device_id).toBe('device123')
  })

  it('should validate CourseSessionStatus', () => {
    const status: CourseSessionStatus = {
      id: 1,
      session_code: 'CS101',
      active: true,
      class_name: '计算机一班',
      teacher_name: '李老师',
      start_time: '2024-01-01T08:00:00Z'
    }

    expect(status.active).toBe(true)
    expect(status.class_name).toBe('计算机一班')
  })
})
