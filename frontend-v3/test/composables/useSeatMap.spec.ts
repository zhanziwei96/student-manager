/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import { mount } from '@vue/test-utils'
import { useSeatMap } from '@/composables/useSeatMap'

vi.mock('@/api/seats', () => ({
  classroomsApi: { getSeats: vi.fn() },
  seatsApi: { setBroken: vi.fn() },
  seatAssignmentsApi: { mine: vi.fn() },
  seatOverridesApi: { set: vi.fn(), clear: vi.fn() },
}))

import { classroomsApi } from '@/api/seats'
const mockedGetSeats = vi.mocked(classroomsApi.getSeats)

function mountComposable(classroomId: number | null, sessionId: number | null) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  let result: ReturnType<typeof useSeatMap> | undefined
  mount({
    setup() {
      result = useSeatMap(ref(classroomId), ref(sessionId))
      return () => null
    },
  }, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
  return result!
}

describe('useSeatMap', () => {
  beforeEach(() => mockedGetSeats.mockReset())

  it('classroomId 为空时不发起请求', () => {
    mountComposable(null, 1)
    expect(mockedGetSeats).not.toHaveBeenCalled()
  })

  it('classroomId + sessionId 都有值时请求座位图', async () => {
    mockedGetSeats.mockResolvedValue({
      classroom: { id: 1, name: '机房302', rows: 2, cols: 2, status: 'active', seat_count: 4 },
      seats: [],
    })
    const { isSuccess } = mountComposable(1, 10)
    await vi.waitFor(() => expect(isSuccess.value).toBe(true))
    expect(mockedGetSeats).toHaveBeenCalledWith(1, 10)
  })
})
