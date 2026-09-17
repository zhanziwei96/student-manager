import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi } from '@/api'
import { toValue, type MaybeRefOrGetter } from 'vue'

export function useTeacherGroups(classId: MaybeRefOrGetter<number | undefined>, courseId?: MaybeRefOrGetter<number | null>) {
  return useQuery({
    queryKey: ['teacher-groups', classId, courseId],
    queryFn: () => groupsApi.getTeacherGroups(toValue(classId)!, toValue(courseId) ?? undefined),
    enabled: () => !!toValue(classId),
  })
}

export function useAutoAssign() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ classId, courseId }: { classId: number; courseId: number }) =>
      groupsApi.autoAssign(classId, courseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-groups'] })
    },
  })
}

export function useStudentGroups(classId: MaybeRefOrGetter<number | undefined>, courseId?: MaybeRefOrGetter<number | null>) {
  return useQuery({
    queryKey: ['student-groups', classId, courseId],
    queryFn: () => groupsApi.getGroups(toValue(classId)!, toValue(courseId) ?? undefined),
    enabled: () => !!toValue(classId),
  })
}

export function useMyGroups() {
  return useQuery({
    queryKey: ['my-groups'],
    queryFn: () => groupsApi.getMyGroups(),
  })
}

export function useCreateGroup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ classId, name, courseId }: { classId: number; name: string; courseId: number }) =>
      groupsApi.createGroup(classId, name, courseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-groups'] })
      queryClient.invalidateQueries({ queryKey: ['student-groups'] })
    },
  })
}

export function useJoinGroup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (groupId: number) => groupsApi.requestJoin(groupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-groups'] })
    },
  })
}

export function useApproveJoin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (reqId: number) => groupsApi.approveJoin(reqId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-groups'] })
    },
  })
}

export function useGroupScore() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ groupId, scoreChange, reason }: { groupId: number; scoreChange: number; reason: string }) =>
      groupsApi.updateScore(groupId, scoreChange, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-groups'] })
    },
  })
}

export function useGroupScoreLogs(groupId: MaybeRefOrGetter<number | null>) {
  return useQuery({
    queryKey: ['group-score-logs', groupId],
    queryFn: () => groupsApi.getScoreLogs(toValue(groupId)!),
    enabled: () => toValue(groupId) !== null,
  })
}
