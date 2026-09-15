/**
 * 列表行左滑操作组合式函数（HIG 手势支持）
 * 行跟手左移，越过阈值驻留展开；同时仅允许一行展开
 * 原生 TouchEvent 实现，仅暴露状态与事件绑定，不渲染 UI
 */
import { ref, readonly } from 'vue'

/**
 * 使用列表行滑动操作
 * @param options.threshold 展开驻留的阈值（px），默认 64
 */
export function useSwipeActions(options?: { threshold?: number }) {
  const threshold = options?.threshold ?? 64

  /** 当前展开的行 id（null 表示全部收起） */
  const openRowId = ref<string | number | null>(null)
  /** 当前行的水平位移（px，负值为左移），页面绑定到活动行的 transform */
  const rowOffset = ref(0)

  let activeId: string | number | null = null
  let startX = 0
  let startY = 0
  let aborted = false

  /** 收起当前展开的行（页面可在点击其他区域时调用） */
  const closeRow = () => {
    openRowId.value = null
    rowOffset.value = 0
  }

  const onTouchstart = (rowId: string | number) => (e: TouchEvent) => {
    // 起手另一行时收起已展开的行
    if (openRowId.value !== null && openRowId.value !== rowId) {
      closeRow()
    }
    activeId = rowId
    aborted = false
    startX = e.touches[0].clientX
    startY = e.touches[0].clientY
  }

  const onTouchmove = (rowId: string | number) => (e: TouchEvent) => {
    if (activeId !== rowId || aborted) return
    const deltaX = e.touches[0].clientX - startX
    const deltaY = e.touches[0].clientY - startY
    // 垂直主导的手势交给滚动，忽略本次滑动
    if (Math.abs(deltaY) > Math.abs(deltaX)) {
      aborted = true
      rowOffset.value = 0
      return
    }
    // 仅响应左滑，跟手位移
    if (deltaX < 0) {
      rowOffset.value = deltaX
    }
  }

  const onTouchend = (rowId: string | number) => () => {
    if (activeId !== rowId) return
    activeId = null
    if (aborted) {
      aborted = false
      return
    }
    if (rowOffset.value <= -threshold) {
      // 越过阈值：驻留展开
      openRowId.value = rowId
      rowOffset.value = -threshold
    } else {
      // 未达阈值：回弹收起
      if (openRowId.value === rowId) openRowId.value = null
      rowOffset.value = 0
    }
  }

  /** 绑定某一行的触摸事件处理器 */
  const bindRow = (rowId: string | number) => ({
    onTouchstart: onTouchstart(rowId),
    onTouchmove: onTouchmove(rowId),
    onTouchend: onTouchend(rowId),
  })

  return {
    bindRow,
    openRowId: readonly(openRowId),
    rowOffset: readonly(rowOffset),
    closeRow,
  }
}
