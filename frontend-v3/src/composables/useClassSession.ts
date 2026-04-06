import { useQuery, useMutation, useQueryClient, type Query } from '@tanstack/vue-query'
import { unref, type Ref, computed } from 'vue'
import { classSessionApi, checkinApi } from '@/api'
import type { CheckinRecord, ClassSessionInfo } from '@/types'

/**
 * REVIEW-P1: SSR 安全工具函数
 * 检查是否在客户端环境
 */
const isClient = (): boolean => typeof window !== 'undefined' && !!window.localStorage

/**
 * REVIEW-P1: SSR 安全的 localStorage 操作
 */
const safeLocalStorage = {
  getItem(key: string): string | null {
    if (!isClient()) return null
    try {
      return localStorage.getItem(key)
    } catch {
      return null
    }
  },
  setItem(key: string, value: string): boolean {
    if (!isClient()) return false
    try {
      localStorage.setItem(key, value)
      return true
    } catch {
      return false
    }
  },
  removeItem(key: string): boolean {
    if (!isClient()) return false
    try {
      localStorage.removeItem(key)
      return true
    } catch {
      return false
    }
  }
}

/**
 * 获取教师所有活跃课堂列表
 * 多班级并行上课支持
 */
export function useClassSessions() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['classSessions'],
    queryFn: async () => {
      // FE-003: 直接获取数据，错误自动抛出
      const sessions = await classSessionApi.getCurrent()
      if (sessions && sessions.length > 0) {
        // REVIEW-P1: 使用 SSR 安全的 localStorage
        safeLocalStorage.setItem('activeClassSessions', JSON.stringify(sessions))
        return sessions
      }

      // 服务器没有活跃课堂，清除 localStorage
      safeLocalStorage.removeItem('activeClassSessions')
      return []
    },
    // 智能刷新策略：有活跃课堂时5秒刷新，否则30秒
    refetchInterval: (query: Query<ClassSessionInfo[], Error, ClassSessionInfo[], string[]>) => {
      const data = query.state.data
      return data && data.length > 0 ? 5000 : 30000
    },
    staleTime: 3000,
    refetchOnWindowFocus: true,
    retry: 0, // 不重试，立即显示错误
  })

  return { data, isPending, error, refetch }
}

/**
 * 获取指定班级的活跃课堂
 * @param className 班级名称
 */
export function useClassSessionByClassName(className: string | Ref<string>) {
  const { data: sessions, isPending, error, refetch } = useClassSessions()

  const data = computed(() => {
    const resolvedClassName = unref(className)
    if (!sessions.value || !resolvedClassName) return null
    return sessions.value.find(s => s.class_name === resolvedClassName) || null
  })

  return { data, isPending, error, refetch }
}

/**
 * 兼容旧版 - 获取第一个活跃课堂（单课堂模式）
 * @deprecated 建议使用 useClassSessions 或 useClassSessionByClassName
 */
export function useClassSession() {
  const { data: sessions, isPending, error, refetch } = useClassSessions()

  const data = computed(() => {
    if (!sessions.value || sessions.value.length === 0) return null
    return sessions.value[0]
  })

  return { data, isPending, error, refetch }
}

export interface StartClassParams {
  className: string
  courseName?: string
}

export function useClassSessionStart() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (params: StartClassParams) => {
      // FE-003: 直接获取数据，错误自动抛出
      const data = await classSessionApi.start({
        class_name: params.className,
        course_name: params.courseName
      })
      return data
    },
    onSuccess: () => {
      // 刷新课堂列表
      queryClient.invalidateQueries({ queryKey: ['classSessions'] })
      // 刷新活跃课堂列表，更新 Dashboard
      queryClient.invalidateQueries({ queryKey: ['active-sessions'] })
    },
  })

  return { mutateAsync, isPending, error }
}

export interface EndClassParams {
  className?: string
}

export function useClassSessionEnd() {
  const queryClient = useQueryClient()

  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (params: EndClassParams = {}) => {
      // FE-003: 直接调用，错误自动抛出
      // 转换参数名称为下划线格式
      await classSessionApi.end({
        class_name: params.className
      })
    },
    onSuccess: () => {
      // 刷新课堂列表
      queryClient.invalidateQueries({ queryKey: ['classSessions'] })
      queryClient.invalidateQueries({ queryKey: ['students'] })
      queryClient.invalidateQueries({ queryKey: ['today-checkins'] })
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
      // 刷新活跃课堂列表，立即更新"其他教师占用"提示
      queryClient.invalidateQueries({ queryKey: ['active-class-sessions'] })
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
      // FE-003: 直接获取数据，错误自动抛出
      return await classSessionApi.getActiveSessions()
    },
    refetchInterval: 10000,
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
      // FE-003: 直接获取数据，错误自动抛出
      return await checkinApi.checkin({
        student_id: studentCode,
        student_name: '',
      })
    },
    onSuccess: () => {
      const resolvedClassName = unref(className)
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
      // FIX: 使用与 useTodayCheckins 相同的查询键格式，确保缓存失效能正确匹配
      queryClient.invalidateQueries({ queryKey: ['today-checkins', resolvedClassName || 'all'] })
    },
  })

  return { mutateAsync, isPending, error }
}
