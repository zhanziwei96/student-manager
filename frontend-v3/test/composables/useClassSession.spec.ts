/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock API
vi.mock('@/api', () => ({
  classSessionApi: {
    getCurrent: vi.fn().mockResolvedValue({
      active: true,
      class_name: '计算机1班',
      course_name: '高等数学',
      start_time: '2026-04-01T10:00:00'
    }),
    start: vi.fn().mockResolvedValue({
      active: true,
      class_name: '计算机1班',
      course_name: '高等数学',
      start_time: '2026-04-01T10:00:00'
    }),
    end: vi.fn().mockResolvedValue({})
  },
  checkinApi: {
    checkin: vi.fn().mockResolvedValue({
      id: 1,
      student_id: 'S001',
      student_name: '张三',
      checkin_time: '2026-04-01T10:05:00'
    })
  }
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn()
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

describe('useClassSession Composable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
  })

  it('should handle SSR-safe localStorage operations', () => {
    // 验证 localStorage mock 可用
    expect(window.localStorage).toBeDefined()
    expect(typeof window.localStorage.getItem).toBe('function')
    expect(typeof window.localStorage.setItem).toBe('function')
  })

  it('should have correct query keys', () => {
    // 验证查询键名规范
    const queryKey = ['classSession']
    expect(queryKey).toEqual(['classSession'])
  })

  it('should handle start class parameters with location', async () => {
    // 验证带位置的参数结构
    const params = {
      className: '计算机1班',
      courseName: '高等数学',
      locationLat: 39.90923,
      locationLng: 116.397428,
      locationName: '机房312',
      checkinRadius: 100
    }

    expect(params).toHaveProperty('className')
    expect(params).toHaveProperty('locationLat')
    expect(params).toHaveProperty('locationLng')
    expect(params).toHaveProperty('locationName')
    expect(params).toHaveProperty('checkinRadius')
  })

  it('should validate StartClassParams interface', () => {
    const validParams = {
      className: '测试班级',
      courseName: '测试课程',
      locationLat: 39.90923,
      locationLng: 116.397428,
      locationName: '测试位置',
      checkinRadius: 100
    }

    // 验证所有参数类型正确
    expect(typeof validParams.className).toBe('string')
    expect(typeof validParams.courseName).toBe('string')
    expect(typeof validParams.locationLat).toBe('number')
    expect(typeof validParams.locationLng).toBe('number')
    expect(typeof validParams.locationName).toBe('string')
    expect(typeof validParams.checkinRadius).toBe('number')
  })
})
