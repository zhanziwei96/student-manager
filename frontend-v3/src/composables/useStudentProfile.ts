import { useQuery } from '@tanstack/vue-query'
import { studentsApi } from '@/api/students'
import { useAuthStore } from '@/stores'
import { computed } from 'vue'

/**
 * 获取当前登录学生的个人信息
 */
export function useStudentProfile() {
  const authStore = useAuthStore()
  const studentId = computed(() => authStore.user?.username || '')

  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['student-profile', studentId],
    queryFn: async () => {
      if (!studentId.value) {
        throw new Error('Not logged in')
      }
      const res = await studentsApi.getByStudentId(studentId.value)
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch student profile')
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
