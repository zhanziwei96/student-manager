/**
 * 学生功能模块类型定义
 *
 * 这些类型专门用于 features/students 模块
 * 与全局类型保持兼容，但提供更细粒度的类型定义
 */

export type { Student } from '@/types'

/**
 * 学生筛选条件
 */
export interface StudentFilterState {
  searchQuery: string
  className: string
}

/**
 * 班级选项
 */
export interface ClassOption {
  value: string
  label: string
  count: number
}
