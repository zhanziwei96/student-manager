import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { studentsApi } from '@/api'
import type { UpdateScoreRequest, CreateStudentRequest, Student } from '@/types'

/**
 * Students query composable - FE-003 修复后
 * 使用统一的 API 响应处理，无需手动检查 res.success
 */
export function useStudents() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['students'],
    queryFn: async () => {
      // FE-003: 直接获取数据，错误自动抛出
      return await studentsApi.getAll()
    },
    // 禁用结构共享，确保 setQueryData 后 UI 立即更新
    structuralSharing: false,
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}

export function useScoreUpdate() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async ({ studentId, data }: { studentId: string; data: UpdateScoreRequest }) => {
      // FE-003: 直接获取数据，错误自动抛出
      return await studentsApi.updateScore(studentId, data)
    },
    onSuccess: async (updatedStudent) => {
      // 获取当前缓存数据
      const currentData = queryClient.getQueryData<Student[]>(['students'])
      
      if (currentData) {
        // 更新缓存中的数据
        const newData = currentData.map((student) =>
          student.student_id === updatedStudent.student_id
            ? { ...student, score: updatedStudent.score }
            : student
        )
        queryClient.setQueryData(['students'], newData)
      }
      
      // 立即强制重新获取，确保数据一致性
      await queryClient.refetchQueries({ queryKey: ['students'], exact: true })
    },
  })

  return {
    mutateAsync,
    isPending,
    error,
  }
}

export function useStudentCreate() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (data: CreateStudentRequest) => {
      // FE-003: 直接获取数据，错误自动抛出
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
