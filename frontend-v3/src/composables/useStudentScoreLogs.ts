import { ref, watch, toValue, type MaybeRefOrGetter } from 'vue'
import { studentsApi } from '@/api/students'
import type { ScoreLog } from '@/types'

interface UseStudentScoreLogsOptions {
  /** 每页条数，默认 20 */
  pageSize?: number
}

/**
 * 获取学生分数历史记录（"加载更多"分页模式）
 *
 * - 初始加载 pageSize 条（最新在前）
 * - loadMore() 追加下一页；返回数量不足 pageSize 时 hasMore 置为 false
 * - studentId 变化时自动重置并重新加载
 */
export function useStudentScoreLogs(
  studentId: MaybeRefOrGetter<string>,
  options?: UseStudentScoreLogsOptions,
) {
  const pageSize = options?.pageSize ?? 20

  const logs = ref<ScoreLog[]>([])
  const isPending = ref(false)
  const isLoadingMore = ref(false)
  const hasMore = ref(true)
  const error = ref<Error | null>(null)
  let offset = 0

  /** 加载一页（首次或追加） */
  async function fetchPage() {
    const id = toValue(studentId)
    if (!id) return

    const isFirst = offset === 0
    if (isFirst) {
      isPending.value = true
    } else {
      isLoadingMore.value = true
    }
    error.value = null

    try {
      const batch = await studentsApi.getScoreLogs(id, { limit: pageSize, offset })
      logs.value = offset === 0 ? batch : [...logs.value, ...batch]
      offset += batch.length
      hasMore.value = batch.length >= pageSize
    } catch (err) {
      error.value = err as Error
    } finally {
      isPending.value = false
      isLoadingMore.value = false
    }
  }

  /** 加载更多（追加下一页） */
  async function loadMore() {
    if (isPending.value || isLoadingMore.value || !hasMore.value) return
    await fetchPage()
  }

  // studentId 就绪/变化时重置并重新加载
  watch(
    () => toValue(studentId),
    (id) => {
      logs.value = []
      offset = 0
      hasMore.value = true
      if (id) fetchPage()
    },
    { immediate: true },
  )

  return { logs, isPending, isLoadingMore, hasMore, error, loadMore }
}
