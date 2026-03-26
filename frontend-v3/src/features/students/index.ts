/**
 * Students Feature Module
 * 
 * 学生管理功能模块，提供学生相关的组件、逻辑和类型
 * 
 * 使用方式:
 * ```ts
 * import { StudentCard, useStudentScore } from '@/features/students'
 * ```
 */

// === 组件 ===
export { default as StudentCard } from './components/StudentCard.vue'
export { default as ScoreDialog } from './components/ScoreDialog.vue'
export { default as QuickScoreButton } from './components/QuickScoreButton.vue'
export { default as StudentFilters } from './components/StudentFilters.vue'

// === Composables ===
export { useStudentScore } from './composables/useStudentScore'
export { useStudentFilters } from './composables/useStudentFilters'

// === 类型 ===
export type {
  Student,
  QuickScoreOption,
  StudentCardConfig,
  StudentFilterState,
  ScoreUpdateEvent,
  GroupedStudents,
  ClassOption,
} from './types'
