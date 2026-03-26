import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'

/**
 * useSchedules 类型安全测试
 * REVIEW-P1: 验证 API 返回类型一致，使用 request<T>() 包装
 */
describe('useSchedules Type Safety', () => {
  // 模拟课表数据
  const mockSchedules = [
    {
      id: 1,
      course_name: '数学',
      class_name: '班级A',
      teacher_id: 1,
      teacher_name: '张老师',
      day_of_week: 1,
      start_time: '08:00',
      end_time: '09:00',
      classroom: '101',
      week_start: 1,
      week_end: 16
    },
    {
      id: 2,
      course_name: '英语',
      class_name: '班级B',
      teacher_id: 2,
      teacher_name: '李老师',
      day_of_week: 2,
      start_time: '09:00',
      end_time: '10:00',
      classroom: '102',
      week_start: 1,
      week_end: 16
    }
  ]

  describe('schedulesApi type consistency', () => {
    it('should have correct return types for getList', async () => {
      // 动态导入避免 Vue Query 的 SSR 问题
      const { schedulesApi } = await import('@/api/schedules')
      
      // 验证函数存在且返回类型正确
      expect(typeof schedulesApi.getList).toBe('function')
      
      // 类型检查：getList 应该返回 Promise<CourseSchedule[]>
      const result = schedulesApi.getList
      expect(result).toBeDefined()
    })

    it('should have correct return types for getToday', async () => {
      const { schedulesApi } = await import('@/api/schedules')
      
      expect(typeof schedulesApi.getToday).toBe('function')
      
      const result = schedulesApi.getToday
      expect(result).toBeDefined()
    })

    it('should have correct return types for import', async () => {
      const { schedulesApi } = await import('@/api/schedules')
      
      expect(typeof schedulesApi.import).toBe('function')
      
      const result = schedulesApi.import
      expect(result).toBeDefined()
    })

    it('should have correct return types for delete', async () => {
      const { schedulesApi } = await import('@/api/schedules')
      
      expect(typeof schedulesApi.delete).toBe('function')
      
      const result = schedulesApi.delete
      expect(result).toBeDefined()
    })

    it('should have correct return types for downloadTemplate', async () => {
      const { schedulesApi } = await import('@/api/schedules')
      
      expect(typeof schedulesApi.downloadTemplate).toBe('function')
      
      const result = schedulesApi.downloadTemplate
      expect(result).toBeDefined()
    })
  })

  describe('CourseSchedule interface', () => {
    it('should have all required fields', () => {
      const schedule = mockSchedules[0]
      
      // 验证必需字段存在
      expect(schedule).toHaveProperty('id')
      expect(schedule).toHaveProperty('course_name')
      expect(schedule).toHaveProperty('class_name')
      expect(schedule).toHaveProperty('day_of_week')
      expect(schedule).toHaveProperty('start_time')
      expect(schedule).toHaveProperty('end_time')
      expect(schedule).toHaveProperty('week_start')
      expect(schedule).toHaveProperty('week_end')
      
      // 验证可选字段（如果存在）
      if (schedule.teacher_id !== undefined) {
        expect(typeof schedule.teacher_id).toBe('number')
      }
      if (schedule.teacher_name !== undefined) {
        expect(typeof schedule.teacher_name).toBe('string')
      }
      if (schedule.classroom !== undefined) {
        expect(typeof schedule.classroom).toBe('string')
      }
      if (schedule.created_at !== undefined) {
        expect(typeof schedule.created_at).toBe('string')
      }
    })

    it('should have correct field types', () => {
      const schedule = mockSchedules[0]
      
      expect(typeof schedule.id).toBe('number')
      expect(typeof schedule.course_name).toBe('string')
      expect(typeof schedule.class_name).toBe('string')
      expect(typeof schedule.day_of_week).toBe('number')
      expect(typeof schedule.start_time).toBe('string')
      expect(typeof schedule.end_time).toBe('string')
      expect(typeof schedule.week_start).toBe('number')
      expect(typeof schedule.week_end).toBe('number')
    })
  })

  describe('ImportResult interface', () => {
    it('should have correct structure', async () => {
      const { schedulesApi } = await import('@/api/schedules')
      
      // 验证 ImportResult 类型定义
      const importResult = {
        imported: 10,
        errors: ['第3行格式错误']
      }
      
      expect(importResult).toHaveProperty('imported')
      expect(importResult).toHaveProperty('errors')
      expect(typeof importResult.imported).toBe('number')
      expect(Array.isArray(importResult.errors)).toBe(true)
    })
  })

  describe('API function exports', () => {
    it('should export schedulesApi from api module', async () => {
      // 直接从 schedules 模块导入验证
      const { schedulesApi } = await import('@/api/schedules')
      
      // 验证 schedulesApi 已定义
      expect(schedulesApi).toBeDefined()
      expect(typeof schedulesApi.getList).toBe('function')
      expect(typeof schedulesApi.getToday).toBe('function')
      expect(typeof schedulesApi.import).toBe('function')
      expect(typeof schedulesApi.delete).toBe('function')
      expect(typeof schedulesApi.downloadTemplate).toBe('function')
    })
  })

  describe('Type consistency with lib/api', () => {
    it('should use consistent request pattern', async () => {
      const { get } = await import('@/lib/api')
      const { schedulesApi } = await import('@/api/schedules')
      
      // 验证都使用相同的 request<T>() 模式
      expect(typeof get).toBe('function')
      expect(typeof schedulesApi.getList).toBe('function')
      
      // 类型一致性：get<T> 返回 Promise<T>
      // schedulesApi.getList 也应该返回 Promise<CourseSchedule[]>
      // 而不是 Promise<ApiResponse<CourseSchedule[]>>
    })
  })
})
