import { useQuery, useMutation, useQueryClient, type Query } from '@tanstack/vue-query'
import { unref, type Ref, computed } from 'vue'
import { courseSessionApi, checkinApi } from '@/api'
import type { CheckinRecord, CourseSession } from '@/types'

const isClient = (): boolean => typeof window !== 'undefined' && !!window.localStorage

const safeLocalStorage = {
  getItem(key: string): string | null {
    if (!isClient()) return null
    try { return localStorage.getItem(key) } catch { return null }
  },
  setItem(key: string, value: string): boolean {
    if (!isClient()) return false
    try { localStorage.setItem(key, value); return true } catch { return false }
  },
  removeItem(key: string): boolean {
    if (!isClient()) return false
    try { localStorage.removeItem(key); return true } catch { return false }
  }
}

export function useCourseSessions() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['courseSessions'],
    queryFn: async () => {
      const sessions = await courseSessionApi.getCurrent()
      if (sessions && sessions.length > 0) {
        safeLocalStorage.setItem('activeCourseSessions', JSON.stringify(sessions))
        return sessions
      }
      safeLocalStorage.removeItem('activeCourseSessions')
      return []
    },
    refetchInterval: (query: Query<CourseSession[], Error, CourseSession[], string[]>) => {
      const data = query.state.data
      return data && data.length > 0 ? 5000 : 30000
    },
    staleTime: 3000,
    refetchOnWindowFocus: true,
    retry: 0,
  })
  return { data, isPending, error, refetch }
}

export function useCourseSessionByClassName(className: string | Ref<string>) {
  const { data: sessions, isPending, error, refetch } = useCourseSessions()
  const data = computed(() => {
    const resolved = unref(className)
    if (!sessions.value || !resolved) return null
    return sessions.value.find(s => s.class_name === resolved) || null
  })
  return { data, isPending, error, refetch }
}

export interface StartCourseSessionParams {
  className: string
  courseName?: string
  scheduleId?: number
}

export function useCourseSessionStart() {
  const queryClient = useQueryClient()
  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (params: StartCourseSessionParams) => {
      return await courseSessionApi.start({
        class_name: params.className,
        course_name: params.courseName,
        schedule_id: params.scheduleId,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courseSessions'] })
      queryClient.invalidateQueries({ queryKey: ['active-class-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['today-schedules'] })
      // 使用 exact: false 匹配所有以 ['session-checkins'] 开头的 query
      queryClient.invalidateQueries({ queryKey: ['session-checkins'], exact: false })
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
    },
  })
  return { mutateAsync, isPending, error }
}

export function useCourseSessionEnd() {
  const queryClient = useQueryClient()
  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (sessionId: number) => {
      await courseSessionApi.end(sessionId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courseSessions'] })
      queryClient.invalidateQueries({ queryKey: ['students'] })
      queryClient.invalidateQueries({ queryKey: ['session-checkins'] })
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
      queryClient.invalidateQueries({ queryKey: ['active-class-sessions'] })
    },
  })
  return { mutateAsync, isPending, error }
}

export function useActiveClassSessions() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['active-class-sessions'],
    queryFn: async () => {
      return await checkinApi.getActiveSessions()
    },
    refetchInterval: 10000,
  })
  return { data, isPending, error, refetch }
}

export function useStudentCheckIn(sessionId?: number | Ref<number | undefined>) {
  const queryClient = useQueryClient()
  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (studentCode: string): Promise<CheckinRecord> => {
      return await checkinApi.checkin({
        student_id: studentCode,
        student_name: '',
      })
    },
    onSuccess: () => {
      const id = unref(sessionId)
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
      queryClient.invalidateQueries({ queryKey: ['session-checkins', id] })
    },
  })
  return { mutateAsync, isPending, error }
}
