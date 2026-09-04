import { describe, it, expect, vi, afterEach } from 'vitest'
import { getCurrentWeek } from '@/lib/date'

describe('getCurrentWeek 学期基准（第二学期改造）', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('开学前返回 0', () => {
    vi.setSystemTime(new Date('2026-09-04T10:00:00'))
    expect(getCurrentWeek('2026-09-07', 20)).toBe(0)
  })

  it('第 1 周返回 1', () => {
    vi.setSystemTime(new Date('2026-09-07T10:00:00'))
    expect(getCurrentWeek('2026-09-07', 20)).toBe(1)
  })

  it('第 2 周返回 2', () => {
    vi.setSystemTime(new Date('2026-09-14T10:00:00'))
    expect(getCurrentWeek('2026-09-07', 20)).toBe(2)
  })

  it('超过总周数封顶', () => {
    vi.setSystemTime(new Date('2027-01-25T10:00:00'))
    expect(getCurrentWeek('2026-09-07', 20)).toBe(20)
  })

  it('无学期基准时返回 1（向后兼容）', () => {
    expect(getCurrentWeek(null, 20)).toBe(1)
  })
})
