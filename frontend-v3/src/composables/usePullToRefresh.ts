/**
 * 下拉刷新组合式函数（HIG 手势支持）
 * 仅暴露状态，不渲染 UI —— 页面自行根据 pullDistance/refreshing 渲染指示器
 * 原生 TouchEvent 实现，仅响应触摸，SSR 安全
 */
import { ref, readonly, onMounted, onUnmounted } from 'vue'
import type { Ref } from 'vue'

/** 阻力系数：手指位移 * 0.4，模拟橡皮筋手感 */
const RESISTANCE = 0.4
/** 下拉距离上限（px） */
const MAX_DISTANCE = 120

/**
 * 使用下拉刷新
 * @param containerRef 滚动容器元素引用（仅在 scrollTop === 0 时触发）
 * @param onRefresh 触发刷新时执行的回调（支持异步）
 * @param options.threshold 触发刷新的阈值（px），默认 80
 */
export function usePullToRefresh(
  containerRef: Ref<HTMLElement | null>,
  onRefresh: () => Promise<unknown> | void,
  options?: { threshold?: number },
) {
  const threshold = options?.threshold ?? 80

  const pulling = ref(false)
  const pullDistance = ref(0)
  const refreshing = ref(false)

  let startY = 0
  let tracking = false

  const reset = () => {
    pulling.value = false
    pullDistance.value = 0
    tracking = false
  }

  const onTouchstart = (e: TouchEvent) => {
    const el = containerRef.value
    // 仅在容器位于顶部时才允许下拉
    if (!el || el.scrollTop !== 0 || refreshing.value) return
    startY = e.touches[0].clientY
    tracking = true
  }

  const onTouchmove = (e: TouchEvent) => {
    if (!tracking) return
    const raw = e.touches[0].clientY - startY
    if (raw > 0) {
      pulling.value = true
      pullDistance.value = Math.min(raw * RESISTANCE, MAX_DISTANCE)
    } else {
      // 上滑时复位，不影响正常滚动
      pulling.value = false
      pullDistance.value = 0
    }
  }

  const onTouchend = async () => {
    if (!tracking) return
    if (pullDistance.value >= threshold) {
      refreshing.value = true
      pullDistance.value = threshold
      try {
        await onRefresh()
      } finally {
        refreshing.value = false
        reset()
      }
    } else {
      // 未达阈值，回弹（页面用过渡动画表现）
      reset()
    }
  }

  onMounted(() => {
    if (typeof window === 'undefined') return
    const el = containerRef.value
    if (!el) return
    el.addEventListener('touchstart', onTouchstart, { passive: true })
    el.addEventListener('touchmove', onTouchmove, { passive: true })
    el.addEventListener('touchend', onTouchend)
  })

  onUnmounted(() => {
    if (typeof window === 'undefined') return
    const el = containerRef.value
    if (!el) return
    el.removeEventListener('touchstart', onTouchstart)
    el.removeEventListener('touchmove', onTouchmove)
    el.removeEventListener('touchend', onTouchend)
  })

  return {
    pulling: readonly(pulling),
    pullDistance: readonly(pullDistance),
    refreshing: readonly(refreshing),
  }
}
