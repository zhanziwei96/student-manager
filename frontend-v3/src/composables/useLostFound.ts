import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { lostFoundApi } from '@/api'
import { useToast } from './useToast'
import type {
  LostFoundQueryParams,
  CreateLostFoundCommentRequest,
  CreateLostFoundClaimRequest,
} from '@/types/lostFound'

// ============== 教师端 Composables ==============

/**
 * 教师端失物招领列表
 */
export function useTeacherLostFoundItems(params?: () => LostFoundQueryParams) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['teacher-lost-found', params?.()],
    queryFn: async () => await lostFoundApi.getTeacherLostFoundItems(params?.()),
    staleTime: 1000 * 60 * 2,
  })

  return { data, isPending, error, refetch }
}

/**
 * 教师端失物招领详情
 */
export function useTeacherLostFoundDetail(id: () => number) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['teacher-lost-found-detail', id()],
    queryFn: async () => await lostFoundApi.getTeacherLostFoundDetail(id()),
    staleTime: 1000 * 60 * 2,
  })

  return { data, isPending, error, refetch }
}

/**
 * 创建失物招领
 */
export function useCreateLostFoundItem() {
  const queryClient = useQueryClient()
  const { success, error: showError } = useToast()

  return useMutation({
    mutationFn: async (data: { title: string; description: string; location?: string; file?: File }) =>
      await lostFoundApi.createLostFoundItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-lost-found'] })
      success('发布成功')
    },
    onError: () => showError('发布失败'),
  })
}

/**
 * 删除失物招领
 */
export function useDeleteLostFoundItem() {
  const queryClient = useQueryClient()
  const { success, error: showError } = useToast()

  return useMutation({
    mutationFn: async (id: number) => await lostFoundApi.deleteLostFoundItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-lost-found'] })
      success('删除成功')
    },
    onError: () => showError('删除失败'),
  })
}

/**
 * 确认认领
 */
export function useConfirmClaim() {
  const queryClient = useQueryClient()
  const { success, error: showError } = useToast()

  return useMutation({
    mutationFn: async ({ itemId, claimId }: { itemId: number; claimId: number }) =>
      await lostFoundApi.confirmClaim(itemId, claimId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-lost-found'] })
      queryClient.invalidateQueries({ queryKey: ['teacher-lost-found-detail'] })
      success('已确认认领')
    },
    onError: () => showError('确认失败'),
  })
}

/**
 * 拒绝认领
 */
export function useRejectClaim() {
  const queryClient = useQueryClient()
  const { success, error: showError } = useToast()

  return useMutation({
    mutationFn: async ({ itemId, claimId }: { itemId: number; claimId: number }) =>
      await lostFoundApi.rejectClaim(itemId, claimId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-lost-found'] })
      queryClient.invalidateQueries({ queryKey: ['teacher-lost-found-detail'] })
      success('已拒绝认领')
    },
    onError: () => showError('拒绝失败'),
  })
}

// ============== 学生端 Composables ==============

/**
 * 学生端失物招领列表
 */
export function useStudentLostFoundItems(params?: () => LostFoundQueryParams) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['student-lost-found', params?.()],
    queryFn: async () => await lostFoundApi.getStudentLostFoundItems(params?.()),
    staleTime: 1000 * 60 * 2,
  })

  return { data, isPending, error, refetch }
}

/**
 * 学生端失物招领详情
 */
export function useStudentLostFoundDetail(id: () => number) {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['student-lost-found-detail', id()],
    queryFn: async () => await lostFoundApi.getStudentLostFoundDetail(id()),
    staleTime: 1000 * 60 * 2,
  })

  return { data, isPending, error, refetch }
}

/**
 * 发表评论
 */
export function useCreateLostFoundComment() {
  const queryClient = useQueryClient()
  const { success, error: showError } = useToast()

  return useMutation({
    mutationFn: async ({ itemId, data }: { itemId: number; data: CreateLostFoundCommentRequest }) =>
      await lostFoundApi.createLostFoundComment(itemId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-lost-found-detail'] })
      success('评论成功')
    },
    onError: () => showError('评论失败'),
  })
}

/**
 * 申请认领
 */
export function useClaimLostFoundItem() {
  const queryClient = useQueryClient()
  const { success, error: showError } = useToast()

  return useMutation({
    mutationFn: async ({ itemId, data }: { itemId: number; data: CreateLostFoundClaimRequest }) =>
      await lostFoundApi.claimLostFoundItem(itemId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-lost-found-detail'] })
      success('申请已提交')
    },
    onError: () => showError('申请失败'),
  })
}
