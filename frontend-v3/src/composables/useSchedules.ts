/**
 * 课表管理 Composables
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { schedulesApi } from '@/api/schedules'
import { computed } from 'vue'

/**
 * 获取课表列表
 */
export function useSchedules(params?: {
  class_name?: string
  teacher_id?: number
  day_of_week?: number
}) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['schedules', params],
    queryFn: async () => {
      const res = await schedulesApi.getList(params)
      return res.data || []
    },
    staleTime: 5 * 60 * 1000,
  })

  return {
    data: computed(() => data.value || []),
    isPending,
    error,
    refetch
  }
}

/**
 * 获取今日课表
 */
export function useTodaySchedules() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['schedules', 'today'],
    queryFn: async () => {
      const res = await schedulesApi.getToday()
      return res.data || []
    },
    staleTime: 1 * 60 * 1000, // 1分钟刷新
  })

  return {
    data: computed(() => data.value || []),
    isPending,
    error,
    refetch
  }
}

/**
 * 导入课表
 */
export function useImportSchedules() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending } = useMutation({
    mutationFn: async (file: File) => {
      const res = await schedulesApi.import(file)
      return res
    },
    onSuccess: () => {
      // 导入成功后刷新课表列表
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
    }
  })

  return {
    mutateAsync,
    isPending
  }
}

/**
 * 删除课程
 */
export function useDeleteSchedule() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending } = useMutation({
    mutationFn: async (id: number) => {
      const res = await schedulesApi.delete(id)
      return res
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
    }
  })

  return {
    mutateAsync,
    isPending
  }
}

/**
 * 下载导入模板
 */
export function useDownloadTemplate() {
  const download = async () => {
    const blob = await schedulesApi.downloadTemplate()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '课表导入模板.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }

  return { download }
}
