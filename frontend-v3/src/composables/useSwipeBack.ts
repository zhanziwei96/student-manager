/**
 * 左缘右滑返回组合式函数（HIG 手势支持）
 * 仅在屏幕左缘 edgeWidth 内起手，避让 iOS 系统边缘手势的惯例
 * 原生 TouchEvent 实现，SSR 安全
 *
 * 注意：深链直接进入的页面无路由历史，router.back() 可能 noop 甚至退出应用；
 * 页面应保留返回按钮作为主要返回途径，本手势仅作增强。
 */
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

/**
 * 使用左缘右滑返回
 * @param options.edgeWidth 左缘响应区宽度（px），默认 24
 * @param options.threshold 触发返回的水平滑动距离（px），默认 100
 */
export function useSwipeBack(options?: { edgeWidth?: number; threshold?: number }) {
  const edgeWidth = options?.edgeWidth ?? 24
  const threshold = options?.threshold ?? 100
  const router = useRouter()

  let startX = 0
  let startY = 0
  let tracking = false

  const onTouchstart = (e: TouchEvent) => {
    const touch = e.touches[0]
    // 必须从屏幕左缘内起手
    if (touch.clientX > edgeWidth) {
      tracking = false
      return
    }
    startX = touch.clientX
    startY = touch.clientY
    tracking = true
  }

  const onTouchend = (e: TouchEvent) => {
    if (!tracking) return
    tracking = false
    const touch = e.changedTouches[0]
    const deltaX = touch.clientX - startX
    const deltaY = touch.clientY - startY
    // 水平主导：位移达阈值且明显大于垂直分量
    if (deltaX >= threshold && deltaX > Math.abs(deltaY) * 2) {
      router.back()
    }
  }

  onMounted(() => {
    if (typeof window === 'undefined') return
    window.addEventListener('touchstart', onTouchstart, { passive: true })
    window.addEventListener('touchend', onTouchend)
  })

  onUnmounted(() => {
    if (typeof window === 'undefined') return
    window.removeEventListener('touchstart', onTouchstart)
    window.removeEventListener('touchend', onTouchend)
  })
}
