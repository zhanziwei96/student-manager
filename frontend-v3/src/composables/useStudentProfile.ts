import { useQuery } from '@tanstack/vue-query'
import { studentsApi } from '@/api/students'
import { useAuthQuery } from '@/composables/useAuth'
import { computed } from 'vue'

/**
 * 获取当前登录学生的个人信息
 *
 * - FE-001: 使用 useAuthQuery 替代 useAuthStore
 * - FE-003: 使用统一的 API 响应处理，无需手动检查 res.success
 */
export function useStudentProfile() {
  const { user } = useAuthQuery()
  const studentId = computed(() => user.value?.username || '')

  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['student-profile', studentId],
    queryFn: async () => {
      if (!studentId.value) {
        throw new Error('Not logged in')
      }
      // FE-003: 直接获取数据，错误自动抛出
      return await studentsApi.getByStudentId(studentId.value)
    },
    enabled: () => !!studentId.value,
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}
