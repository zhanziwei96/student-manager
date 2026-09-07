import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi } from '@/api'
import { toValue, type MaybeRefOrGetter } from 'vue'

export function useTeacherGroups(className: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: ['teacher-groups', className],
    queryFn: () => groupsApi.getTeacherGroups(toValue(className)),
    enabled: () => !!toValue(className),
  })
}

export function useAutoAssign() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ className }: { className: string }) =>
      groupsApi.autoAssign(className),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-groups'] })
    },
  })
}

export function useStudentGroups(className: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: ['student-groups', className],
    queryFn: () => groupsApi.getGroups(toValue(className)),
    enabled: () => !!toValue(className),
  })
}

export function useMyGroup() {
  return useQuery({
    queryKey: ['my-group'],
    queryFn: () => groupsApi.getMyGroup(),
  })
}

export function useCreateGroup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ className, name, subjectId }: { className: string; name: string; subjectId?: number }) =>
      groupsApi.createGroup(className, name, subjectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-group'] })
      queryClient.invalidateQueries({ queryKey: ['student-groups'] })
    },
  })
}

export function useJoinGroup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (groupId: number) => groupsApi.requestJoin(groupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-group'] })
    },
  })
}

export function useApproveJoin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (reqId: number) => groupsApi.approveJoin(reqId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-group'] })
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
      queryClient.invalidateQueries({ queryKey: ['group-leaderboard'] })
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

export function useGroupLeaderboard(
  subjectId: MaybeRefOrGetter<number | null>,
  className: MaybeRefOrGetter<string>,
) {
  return useQuery({
    queryKey: ['group-leaderboard', className, subjectId],
    queryFn: () => groupsApi.getLeaderboard({
      subject_id: toValue(subjectId) ?? undefined,
      class_name: toValue(className),
    }),
    enabled: () => !!toValue(className),
  })
}
