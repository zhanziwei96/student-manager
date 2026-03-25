import type { Student } from '@/types'

/**
 * Students Feature 专用类型
 * 
 * FE-005: Feature-based 组织示例
 * 这些类型专门用于学生管理功能模块
 */

/**
 * 学生表单数据
 * 用于创建/编辑学生
 */
export interface StudentFormData {
  student_id: string
  name: string
  class_name: string
  score?: number
}

/**
 * 分数更新数据
 */
export interface ScoreUpdateData {
  score_change: number
  reason: string
}

/**
 * 学生列表筛选条件
 */
export interface StudentListFilters {
  class_name?: string
  search?: string
  is_active?: boolean
}

/**
 * 学生统计信息
 */
export interface StudentStats {
  total: number
  active: number
  average_score: number
  class_distribution: Record<string, number>
}
