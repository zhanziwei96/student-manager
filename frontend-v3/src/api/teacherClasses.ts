import { get, put } from '@/lib/api'
import type { ClassInfo } from './classes'

/**
 * 老师班级管理 API
 *
 * 业务纠正后：老师自己决定教哪些班级（不再由管理员修改 assigned_classes）。
 * - GET /teacher/classes 获取当前老师教的班级列表
 * - PUT /teacher/classes 保存老师负责的班级列表（添加/移除）
 * - GET /classes 获取全部班级供选择
 */
export const teacherClassesApi = {
  /** 获取当前老师教的班级列表 */
  getMine: (): Promise<string[]> => get('/teacher/classes'),

  /** 保存老师教的班级列表（添加/移除） */
  updateMine: (classNames: string[]): Promise<void> =>
    put('/teacher/classes', { class_names: classNames }),

  /** 获取全部班级供选择 */
  getAll: (): Promise<ClassInfo[]> => get('/classes'),
}
