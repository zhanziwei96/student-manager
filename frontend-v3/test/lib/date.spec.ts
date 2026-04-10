/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { formatDistanceToNow, formatDateTime, formatDate, formatTime, getCurrentWeek } from '@/lib/date'

describe('Date Utils', () => {
  describe('formatDistanceToNow', () => {
    it('should return "刚刚" for recent time', () => {
      const now = new Date()
      expect(formatDistanceToNow(now)).toBe('刚刚')
    })

    it('should return minutes ago', () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000)
      expect(formatDistanceToNow(fiveMinutesAgo)).toBe('5分钟前')
    })

    it('should return hours ago', () => {
      const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000)
      expect(formatDistanceToNow(twoHoursAgo)).toBe('2小时前')
    })

    it('should return days ago', () => {
      const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)
      expect(formatDistanceToNow(threeDaysAgo)).toBe('3天前')
    })
  })

  describe('formatDateTime', () => {
    it('should format date time correctly', () => {
      const date = new Date('2024-03-15 14:30:00')
      const result = formatDateTime(date)
      expect(result).toContain('2024')
      expect(result).toContain('03')
      expect(result).toContain('15')
    })
  })

  describe('formatDate', () => {
    it('should format date correctly', () => {
      const date = new Date('2024-03-15')
      const result = formatDate(date)
      expect(result).toContain('2024')
      expect(result).toContain('3')
      expect(result).toContain('15')
    })
  })

  describe('formatTime', () => {
    it('should format time correctly', () => {
      const date = new Date('2024-03-15 14:30:00')
      const result = formatTime(date)
      expect(result).toContain('14')
      expect(result).toContain('30')
    })
  })

  describe('getCurrentWeek', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('should return reference week at baseline Monday', () => {
      vi.setSystemTime(new Date('2026-03-30'))
      expect(getCurrentWeek()).toBe(4)
    })

    it('should return next week one week after baseline', () => {
      vi.setSystemTime(new Date('2026-04-06'))
      expect(getCurrentWeek()).toBe(5)
    })

    it('should return previous week one week before baseline', () => {
      vi.setSystemTime(new Date('2026-03-23'))
      expect(getCurrentWeek()).toBe(3)
    })

    it('should return at least week 1', () => {
      vi.setSystemTime(new Date('2020-01-01'))
      expect(getCurrentWeek()).toBeGreaterThanOrEqual(1)
    })
  })
})
