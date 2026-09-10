/**
 * Students Feature Module
 *
 * 学生管理功能模块，提供学生列表的筛选组件与分页逻辑
 *
 * 使用方式:
 * ```ts
 * import { StudentFilters, usePaginatedStudents } from '@/features/students'
 * ```
 */

// === 组件 ===
export { default as StudentFilters } from './components/StudentFilters.vue'

// === Composables ===
export { usePaginatedStudents } from './composables/usePaginatedStudents'

// === 类型 ===
export type {
  Student,
  StudentFilterState,
  ClassOption,
} from './types'
