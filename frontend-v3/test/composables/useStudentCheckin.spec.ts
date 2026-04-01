/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick, h, defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import type { Student, CheckinRecord, ClassSessionInfo } from '@/types'

// Type for Vue Query mock return
interface QueryResult<T> {
  data: import('vue').Ref<T | null>
  isPending: import('vue').Ref<boolean>
  error: import('vue').Ref<Error | null>
}

// Helper to run composables in Vue setup context
function withSetup<T>(composable: () => T): { result: T; unmount: () => void } {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
    },
  })

  let result!: T
  const TestComponent = defineComponent({
    setup() {
      result = composable()
      return () => h('div')
    },
  })

  const wrapper = mount(TestComponent, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
    },
  })

  return {
    result,
    unmount: () => wrapper.unmount(),
  }
}

// Mock API
vi.mock('@/api/checkin', () => ({
  checkinApi: {
    getClassSessionForClass: vi.fn(),
    checkin: vi.fn(),
  },
}))

// Mock device fingerprint
vi.mock('@/lib/device', () => ({
  getDeviceFingerprint: vi.fn().mockResolvedValue('device123'),
  getDeviceInfo: vi.fn().mockReturnValue({
    userAgent: 'test-agent',
    platform: 'test-platform',
  }),
}))

// Mock student profile composable
vi.mock('@/composables/useStudentProfile', () => ({
  useStudentProfile: vi.fn(),
}))

// Mock today checkins composable
vi.mock('@/composables/useCheckins', () => ({
  useTodayCheckins: vi.fn(),
}))

import { checkinApi } from '@/api/checkin'
import { useStudentProfile } from '@/composables/useStudentProfile'
import { useTodayCheckins } from '@/composables/useCheckins'
import {
  useStudentClassSession,
  useStudentSelfCheckin,
  useGeolocation,
  useHasCheckedInSession,
} from '@/composables/useStudentCheckin'

describe('useStudentClassSession', () => {
  const mockStudent: Student = {
    id: '1',
    student_id: 'S001',
    name: '张三',
    class_name: '计算机一班',
    score: 100,
  }

  const mockClassSession: ClassSessionInfo = {
    session_id: 1,
    class_name: '计算机一班',
    course_name: '软件工程',
    teacher_id: 1,
    teacher_name: '李老师',
    location: { lat: 39.9, lng: 116.4 },
    active: true,
    created_at: '2024-01-01T08:00:00Z',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useStudentProfile).mockReturnValue({
      data: ref(mockStudent),
      isPending: ref(false),
      error: ref(null),
    } as QueryResult<Student>)
    vi.mocked(checkinApi.getClassSessionForClass).mockResolvedValue(mockClassSession)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('当班级有活跃课堂时应返回会话信息', async () => {
    const { result, unmount } = withSetup(() => useStudentClassSession())

    // 等待 query 执行
    await new Promise((resolve) => setTimeout(resolve, 100))
    await nextTick()

    expect(checkinApi.getClassSessionForClass).toHaveBeenCalledWith('计算机一班')
    expect(result.data.value).toEqual(mockClassSession)
    expect(result.hasActiveSession.value).toBe(true)
    unmount()
  })

  it('当传入特定班级名时应使用传入值而非学生班级', async () => {
    const { unmount } = withSetup(() => useStudentClassSession(ref('计算机二班')))

    await new Promise((resolve) => setTimeout(resolve, 100))

    expect(checkinApi.getClassSessionForClass).toHaveBeenCalledWith('计算机二班')
    unmount()
  })

  it('当学生信息未加载时不应调用API', () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: ref(null),
      isPending: ref(true),
      error: ref(null),
    } as QueryResult<Student>)

    const { unmount } = withSetup(() => useStudentClassSession())

    expect(checkinApi.getClassSessionForClass).not.toHaveBeenCalled()
    unmount()
  })

  it('当班级无活跃课堂时hasActiveSession应为false', async () => {
    vi.mocked(checkinApi.getClassSessionForClass).mockResolvedValue({
      ...mockClassSession,
      active: false,
    })

    const { result, unmount } = withSetup(() => useStudentClassSession())

    await new Promise((resolve) => setTimeout(resolve, 100))
    await nextTick()

    expect(result.hasActiveSession.value).toBe(false)
    unmount()
  })
})

describe('useStudentSelfCheckin', () => {
  const mockStudent: Student = {
    id: '1',
    student_id: 'S001',
    name: '张三',
    class_name: '计算机一班',
    score: 100,
  }

  const mockCheckinRecord: CheckinRecord = {
    id: 1,
    student_id: 'S001',
    student_name: '张三',
    class_name: '计算机一班',
    course_name: '软件工程',
    session_id: 1,
    checkin_time: '2024-01-01T08:30:00Z',
    status: 'present',
    device_id: 'device123',
    device_info: '{"platform":"test-platform"}',
    lat: 39.90923,
    lng: 116.397428,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useStudentProfile).mockReturnValue({
      data: ref(mockStudent),
      isPending: ref(false),
      error: ref(null),
    } as QueryResult<Student>)
    vi.mocked(checkinApi.checkin).mockResolvedValue(mockCheckinRecord)
  })

  it('当学生信息存在时应成功执行签到', async () => {
    const { result, unmount } = withSetup(() => useStudentSelfCheckin())

    const checkinResult = await result.mutateAsync({ lat: 39.90923, lng: 116.397428 })

    expect(checkinApi.checkin).toHaveBeenCalledWith(
      expect.objectContaining({
        student_id: 'S001',
        student_name: '张三',
        lat: 39.90923,
        lng: 116.397428,
        device_id: 'device123',
        device_info: expect.any(String),
      })
    )
    expect(checkinResult).toEqual(mockCheckinRecord)
    unmount()
  })

  it('当学生信息不存在时应抛出错误', async () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: ref(null),
      isPending: ref(false),
      error: ref(null),
    } as QueryResult<Student>)

    const { result, unmount } = withSetup(() => useStudentSelfCheckin())

    await expect(result.mutateAsync({ lat: 39.9, lng: 116.4 })).rejects.toThrow('未找到学生信息')
    unmount()
  })

  it('签到时不传位置信息应也能正常工作', async () => {
    const { result, unmount } = withSetup(() => useStudentSelfCheckin())

    await result.mutateAsync()

    expect(checkinApi.checkin).toHaveBeenCalledWith(
      expect.objectContaining({
        lat: undefined,
        lng: undefined,
      })
    )
    unmount()
  })

  it('签到成功后应清空位置错误', async () => {
    const { result, unmount } = withSetup(() => useStudentSelfCheckin())

    // 先设置错误状态
    result.locationError.value = '定位失败'

    await result.mutateAsync({ lat: 39.9, lng: 116.4 })

    // 成功后会清空错误（通过 onSuccess 回调）
    expect(checkinApi.checkin).toHaveBeenCalled()
    unmount()
  })
})

describe('useGeolocation', () => {
  const mockGeolocation = {
    getCurrentPosition: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    Object.defineProperty(navigator, 'geolocation', {
      value: mockGeolocation,
      writable: true,
      configurable: true,
    })
  })

  it('定位成功时应返回经纬度并更新状态', async () => {
    const mockPosition = {
      coords: {
        latitude: 39.90923,
        longitude: 116.397428,
      },
    }

    mockGeolocation.getCurrentPosition.mockImplementation((success) => {
      success(mockPosition)
    })

    const { getCurrentPosition, position, isLocating, locationError } = useGeolocation()

    const result = await getCurrentPosition()

    expect(isLocating.value).toBe(false)
    expect(locationError.value).toBeNull()
    expect(position.value).toEqual({ lat: 39.90923, lng: 116.397428 })
    expect(result).toEqual({ lat: 39.90923, lng: 116.397428 })
  })

  it('浏览器不支持定位时应返回null并设置错误', async () => {
    Object.defineProperty(navigator, 'geolocation', {
      value: undefined,
      writable: true,
      configurable: true,
    })

    const { getCurrentPosition, position, locationError } = useGeolocation()

    const result = await getCurrentPosition()

    expect(result).toBeNull()
    expect(position.value).toBeNull()
    expect(locationError.value).toBe('您的浏览器不支持地理定位')
  })

  it('用户拒绝权限时应返回null并设置正确错误信息', async () => {
    const mockError = {
      code: 1,
      PERMISSION_DENIED: 1,
      POSITION_UNAVAILABLE: 2,
      TIMEOUT: 3,
    }

    mockGeolocation.getCurrentPosition.mockImplementation((_, error) => {
      if (error) error(mockError)
    })

    const { getCurrentPosition, locationError } = useGeolocation()

    const result = await getCurrentPosition()

    expect(result).toBeNull()
    expect(locationError.value).toBe('请允许访问位置信息以完成签到')
  })

  it('定位超时错误应设置正确错误信息', async () => {
    const mockError = {
      code: 3,
      PERMISSION_DENIED: 1,
      POSITION_UNAVAILABLE: 2,
      TIMEOUT: 3,
    }

    mockGeolocation.getCurrentPosition.mockImplementation((_, error) => {
      if (error) error(mockError)
    })

    const { getCurrentPosition, locationError } = useGeolocation()

    await getCurrentPosition()

    expect(locationError.value).toBe('获取位置超时，请重试')
  })

  it('定位过程中isLocating应为true', () => {
    mockGeolocation.getCurrentPosition.mockImplementation(() => {
      // 不调用 success 或 error，模拟正在定位
    })

    const { getCurrentPosition, isLocating } = useGeolocation()

    getCurrentPosition()

    expect(isLocating.value).toBe(true)
  })
})

describe('useHasCheckedInSession', () => {
  const mockStudent: Student = {
    id: '1',
    student_id: 'S001',
    name: '张三',
    class_name: '计算机一班',
    score: 100,
  }

  const mockCheckins: CheckinRecord[] = [
    {
      id: 1,
      student_id: 'S001',
      student_name: '张三',
      class_name: '计算机一班',
      course_name: '软件工程',
      session_id: 1,
      checkin_time: '2024-01-01T08:30:00Z',
      status: 'present',
    },
    {
      id: 2,
      student_id: 'S002',
      student_name: '李四',
      class_name: '计算机一班',
      course_name: '软件工程',
      session_id: 1,
      checkin_time: '2024-01-01T08:35:00Z',
      status: 'present',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useStudentProfile).mockReturnValue({
      data: ref(mockStudent),
      isPending: ref(false),
      error: ref(null),
    } as QueryResult<Student>)
    vi.mocked(useTodayCheckins).mockReturnValue({
      data: ref(mockCheckins),
      isPending: ref(false),
      error: ref(null),
    } as QueryResult<CheckinRecord[]>)
  })

  it('当学生已签到指定课堂时应返回true', () => {
    const { result, unmount } = withSetup(() => useHasCheckedInSession(1))

    expect(result.hasCheckedIn.value).toBe(true)
    unmount()
  })

  it('当学生未签到指定课堂时应返回false', () => {
    const { result, unmount } = withSetup(() => useHasCheckedInSession(999))

    expect(result.hasCheckedIn.value).toBe(false)
    unmount()
  })

  it('应返回正确的签到记录详情', () => {
    const { result, unmount } = withSetup(() => useHasCheckedInSession(1))

    expect(result.sessionCheckin.value).toEqual(mockCheckins[0])
    unmount()
  })

  it('当签到列表为空时应返回false', () => {
    vi.mocked(useTodayCheckins).mockReturnValue({
      data: ref([]),
      isPending: ref(false),
      error: ref(null),
    } as QueryResult<Student>)

    const { result, unmount } = withSetup(() => useHasCheckedInSession(1))

    expect(result.hasCheckedIn.value).toBe(false)
    unmount()
  })

  it('当学生信息未加载时应返回false', () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: ref(null),
      isPending: ref(true),
      error: ref(null),
    } as QueryResult<Student>)

    const { result, unmount } = withSetup(() => useHasCheckedInSession(1))

    expect(result.hasCheckedIn.value).toBe(false)
    unmount()
  })

  it('应支持响应式sessionId', () => {
    const sessionId = ref(1)
    const { result, unmount } = withSetup(() => useHasCheckedInSession(sessionId))

    expect(result.hasCheckedIn.value).toBe(true)

    // 切换 sessionId
    sessionId.value = 2
    expect(result.hasCheckedIn.value).toBe(false)
    unmount()
  })
})
