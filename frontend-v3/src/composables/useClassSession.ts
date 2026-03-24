import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { unref, type Ref } from 'vue'
import { classSessionApi, checkinApi } from '@/api'
import type { CheckinRecord } from '@/types'

/**
 * Class Session composable
 * Based on: https://github.com/tanstack/query
 */
export function useClassSession() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['classSession'],
    queryFn: async () => {
      // 优先从服务器 API 获取真实状态
      const res = await classSessionApi.getCurrent()
      if (res.success && res.data && res.data.active) {
        // 同步到 localStorage
        localStorage.setItem('activeClassSession', JSON.stringify(res.data))
        return res.data
      }
      
      // 服务器没有活跃课堂，清除 localStorage
      localStorage.removeItem('activeClassSession')
      return null
    },
    staleTime: 5000, // 5秒后重新获取
    refetchOnWindowFocus: true, // 窗口聚焦时重新获取
  })

  return { data, isPending, error, refetch }
}

export function useClassSessionStart() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (className: string) => {
      const res = await classSessionApi.start({ class_name: className })
      if (res.success && res.data) {
        localStorage.setItem('activeClassSession', JSON.stringify(res.data))
        return res.data
      }
      throw new Error(res.message || 'Failed to start class')
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['classSession'], data)
    },
  })

  return { mutateAsync, isPending, error }
}

export function useClassSessionEnd() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async () => {
      const res = await classSessionApi.end()
      if (!res.success) {
        throw new Error(res.message || 'Failed to end class')
      }
      localStorage.removeItem('activeClassSession')
    },
    onSuccess: () => {
      queryClient.setQueryData(['classSession'], null)
      // 刷新学生列表，使活跃状态重置
      queryClient.invalidateQueries({ queryKey: ['students'] })
      // 刷新签到记录
      queryClient.invalidateQueries({ queryKey: ['today-checkins'] })
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
    },
  })

  return { mutateAsync, isPending, error }
}

/**
 * 获取所有活跃课堂列表
 */
export function useActiveClassSessions() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['active-class-sessions'],
    queryFn: async () => {
      const res = await classSessionApi.getActiveSessions()
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || 'Failed to fetch active sessions')
    },
    refetchInterval: 10000, // 每10秒刷新一次
  })

  return {
    data,
    isPending,
    error,
    refetch,
  }
}

export function useStudentCheckIn(className?: string | Ref<string>) {
  const queryClient = useQueryClient()
  
  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (studentCode: string): Promise<CheckinRecord> => {
      // 直接调用签到API，后端会验证学生存在性
      const res = await checkinApi.checkin({
        student_id: studentCode,
        student_name: '', // 后端会根据student_id查找
      })
      
      if (res.success && res.data) {
        return res.data
      }
      throw new Error(res.message || '签到失败')
    },
    onSuccess: () => {
      // 刷新签到统计 - 必须包含 className 才能匹配缓存
      const resolvedClassName = unref(className)  // 解包 ComputedRef
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
      if (resolvedClassName) {
        queryClient.invalidateQueries({ queryKey: ['today-checkins', resolvedClassName] })
      } else {
        queryClient.invalidateQueries({ queryKey: ['today-checkins'] })
      }
    },
  })

  return { mutateAsync, isPending, error }
}
