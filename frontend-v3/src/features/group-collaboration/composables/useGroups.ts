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
    mutationFn: ({ className, name }: { className: string; name: string }) =>
      groupsApi.createGroup(className, name),
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
