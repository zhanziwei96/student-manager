/**
 * 学生功能模块类型定义
 * 
 * 这些类型专门用于 features/students 模块
 * 与全局类型保持兼容，但提供更细粒度的类型定义
 */

import type { Student } from '@/types'

// 重新导出 Student 类型，让组件可以从本模块导入
export type { Student }

/**
 * 快速分数选项
 */
export interface QuickScoreOption {
  label: string
  score: number
  icon: string  // 使用图标名称，组件中解析为实际图标组件
}

/**
 * 学生卡片展示配置
 */
export interface StudentCardConfig {
  showCheckinStatus: boolean
  showQuickActions: boolean
  showScoreEdit: boolean
}

/**
 * 学生筛选条件
 */
export interface StudentFilterState {
  searchQuery: string
  className: string
}

/**
 * 分数更新事件
 */
export interface ScoreUpdateEvent {
  student: Student
  scoreChange: number
  reason: string
}

/**
 * 学生分组结果
 */
export interface GroupedStudents {
  [className: string]: Student[]
}

/**
 * 班级选项
 */
export interface ClassOption {
  value: string
  label: string
  count: number
}
