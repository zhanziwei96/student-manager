import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'
import { studentsApi } from '@/api'
import type { UpdateScoreRequest, CreateStudentRequest, Student } from '@/types'

/**
 * Students query composable - FE-006 修复
 * 使用统一的 API 响应处理，无需手动检查 res.success
 */
export function useStudents() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['students'],
    queryFn: async () => {
      return await studentsApi.getAll()
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}

/**
 * 乐观更新上下文类型
 */
interface ScoreUpdateContext {
  previousStudents: Student[] | undefined
}

/**
 * 分数更新 composable - FE-006 修复
 * 
 * 使用正确的乐观更新模式（Context7 推荐）：
 * 1. onMutate: 立即更新 UI，保存旧数据用于回滚
 * 2. onError: 出错时回滚到旧数据
 * 3. onSettled: 无论成功与否，最终同步服务器数据
 */
export function useScoreUpdate() {
  const queryClient = useQueryClient()

  const mutation = useMutation<Student, Error, { studentId: string; data: UpdateScoreRequest }, ScoreUpdateContext>({
    mutationFn: async ({ studentId, data }) => {
      return await studentsApi.updateScore(studentId, data)
    },

    /**
     * 乐观更新 - 在请求发送前立即更新 UI
     */
    onMutate: async ({ studentId, data }) => {
      // 取消正在进行的重新获取，避免覆盖我们的乐观更新
      await queryClient.cancelQueries({ queryKey: ['students'] })

      // 保存当前数据用于出错时回滚
      const previousStudents = queryClient.getQueryData<Student[]>(['students'])

      // 乐观更新缓存
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

      // 返回上下文，用于 onError 回滚
      return { previousStudents }
    },

    /**
     * 错误处理 - 回滚到旧数据
     */
    onError: (_err, _variables, context) => {
      if (context?.previousStudents) {
        queryClient.setQueryData(['students'], context.previousStudents)
      }
    },

    /**
     * 完成处理 - 无论成功与否，同步服务器数据
     */
    onSettled: (data) => {
      // 使缓存失效，触发重新获取以同步服务器数据
      queryClient.invalidateQueries({ queryKey: ['students'] })
      
      // 同时更新单个学生的缓存（如果存在）
      if (data) {
        queryClient.setQueryData(['student', data.student_id], data)
      }
    },
  })

  return {
    mutateAsync: mutation.mutateAsync,
    isPending: mutation.isPending,
    error: mutation.error,
    // 暴露当前正在更新的变量，用于 UI 显示加载状态
    updatingStudentId: computed(() => mutation.variables.value?.studentId),
  }
}

export function useStudentCreate() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (data: CreateStudentRequest) => {
      return await studentsApi.create(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  return {
    mutateAsync,
    isPending,
    error,
  }
}
