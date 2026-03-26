import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { studentsApi } from '@/api'
import type { Student, UpdateScoreRequest } from '@/types'
import { ref } from 'vue'

/**
 * 乐观更新上下文类型
 */
interface ScoreUpdateContext {
  previousStudents: Student[] | undefined
  previousStudent: Student | undefined
}

/**
 * 学生分数管理 Composable - FE-006 实现
 * 
 * 使用 TanStack Query 乐观更新模式：
 * - onMutate: 立即更新 UI，保存旧数据
 * - onError: 出错时回滚
 * - onSettled: 最终同步服务器数据
 * 
 * 参考: Context7 TanStack Query v5 文档
 */
export function useStudentScore() {
  const queryClient = useQueryClient()
  
  // 当前正在更新的学生ID（用于UI显示加载状态）
  const updatingStudentId = ref<string | null>(null)

  const scoreMutation = useMutation<
    Student,
    Error,
    { studentId: string; data: UpdateScoreRequest },
    ScoreUpdateContext
  >({
    mutationFn: async ({ studentId, data }) => {
      return await studentsApi.updateScore(studentId, data)
    },

    /**
     * 乐观更新 - 请求发送前立即更新 UI
     */
    onMutate: async ({ studentId, data }) => {
      // 设置当前更新的学生ID
      updatingStudentId.value = studentId

      // 取消正在进行的重新获取
      await queryClient.cancelQueries({ queryKey: ['students'] })
      await queryClient.cancelQueries({ queryKey: ['student', studentId] })

      // 保存当前数据用于回滚
      const previousStudents = queryClient.getQueryData<Student[]>(['students'])
      const previousStudent = queryClient.getQueryData<Student>(['student', studentId])

      // 乐观更新学生列表缓存
      if (previousStudents) {
        queryClient.setQueryData<Student[]>(['students'], (old) => {
          if (!old) return old
          return old.map((student) =>
            student.student_id === studentId
              ? { ...student, score: student.score + data.score_change }
              : student
          )
        })
      }

      // 乐观更新单个学生缓存
      if (previousStudent) {
        queryClient.setQueryData<Student>(['student', studentId], {
          ...previousStudent,
          score: previousStudent.score + data.score_change,
        })
      }

      return { previousStudents, previousStudent }
    },

    /**
     * 错误处理 - 回滚到旧数据
     */
    onError: (_err, variables, context) => {
      if (context?.previousStudents) {
        queryClient.setQueryData(['students'], context.previousStudents)
      }
      if (context?.previousStudent) {
        queryClient.setQueryData(['student', variables.studentId], context.previousStudent)
      }
    },

    /**
     * 完成处理 - 同步服务器数据
     */
    onSettled: (data, _error, variables) => {
      updatingStudentId.value = null
      
      // 使缓存失效，触发重新获取
      queryClient.invalidateQueries({ queryKey: ['students'] })
      queryClient.invalidateQueries({ queryKey: ['student', variables.studentId] })
      
      // 更新单个学生缓存
      if (data) {
        queryClient.setQueryData(['student', data.student_id], data)
      }
    },
  })

  /**
   * 更新分数
   */
  const updateScore = async (
    studentId: string, 
    scoreChange: number, 
    reason: string
  ): Promise<Student> => {
    return scoreMutation.mutateAsync({
      studentId,
      data: { score_change: scoreChange, reason },
    })
  }

  return {
    updateScore,
    isUpdating: scoreMutation.isPending,
    error: scoreMutation.error,
    updatingStudentId,
  }
}
