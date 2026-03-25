/**
 * Students Feature
 * 
 * 学生管理功能模块
 * 包含学生列表、添加、编辑、删除、分数管理等功能
 * 
 * FE-005: Feature-based 组织示例
 * 
 * 使用方式:
 * ```ts
 * import { StudentList, useStudentForm } from '@/features/students'
 * ```
 * 
 * 注意: 这是 FE-005 修复创建的示例结构
 * 实际组件迁移将在后续迭代中逐步进行
 */

// 类型导出
export type { 
  StudentFormData, 
  ScoreUpdateData, 
  StudentListFilters,
  StudentStats 
} from './types'

// TODO: 组件迁移完成后取消注释
// export { default as StudentList } from './components/StudentList.vue'
// export { default as StudentForm } from './components/StudentForm.vue'
// export { default as ScoreDialog } from './components/ScoreDialog.vue'

// TODO: composables 迁移完成后取消注释  
// export { useStudentForm } from './composables/useStudentForm'
// export { useScoreUpdate } from './composables/useScoreUpdate'
