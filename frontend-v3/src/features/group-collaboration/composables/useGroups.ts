import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi } from '@/api'
import { toValue, type MaybeRefOrGetter } from 'vue'

export function useTeacherGroups(className: MaybeRefOrGetter<string>, courseId?: MaybeRefOrGetter<number | null>) {
  return useQuery({
    queryKey: ['teacher-groups', className, courseId],
    queryFn: () => groupsApi.getTeacherGroups(toValue(className), toValue(courseId) ?? undefined),
    enabled: () => !!toValue(className),
  })
}

export function useAutoAssign() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ className, courseId }: { className: string; courseId: number }) =>
      groupsApi.autoAssign(className, courseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-groups'] })
    },
  })
}

export function useStudentGroups(className: MaybeRefOrGetter<string>, courseId?: MaybeRefOrGetter<number | null>) {
  return useQuery({
    queryKey: ['student-groups', className, courseId],
    queryFn: () => groupsApi.getGroups(toValue(className), toValue(courseId) ?? undefined),
    enabled: () => !!toValue(className),
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
    mutationFn: ({ className, name, courseId }: { className: string; name: string; courseId: number }) =>
      groupsApi.createGroup(className, name, courseId),
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
