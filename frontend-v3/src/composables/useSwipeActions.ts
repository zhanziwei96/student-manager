/**
 * 列表行左滑操作组合式函数（HIG 手势支持）
 * 行跟手左移，越过半阈值驻留展开；同时仅允许一行展开
 * 原生 TouchEvent 实现，仅暴露状态与事件绑定，不渲染 UI
 *
 * 页面绑定 transform 的推荐写法：
 *   activeRowId.value === rowId
 *     ? rowOffset.value            // 手势进行中：跟手
 *     : (openRowId.value === rowId ? -threshold : 0)  // 展开驻留 / 收起
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
  /** 手势进行中的行 id（松手后归 null），页面据此决定 rowOffset 绑到哪行 */
  const activeRowId = ref<string | number | null>(null)
  /** 活动行的水平位移（px，负值为左移），已 clamp，页面绑定到活动行的 transform */
  const rowOffset = ref(0)

  let startX = 0
  let startY = 0
  /** 手势起始基线：已展开行从 -threshold 起算，避免跳变并支持右滑关闭 */
  let baseOffset = 0
  let aborted = false

  /** 收起当前展开的行（页面可在点击其他区域时调用） */
  const closeRow = () => {
    openRowId.value = null
    rowOffset.value = 0
  }

  /** 位移上限：最多比展开位多滑出半个操作区，下限为 0 */
  const clamp = (v: number) => Math.max(Math.min(baseOffset - threshold, -threshold * 1.5), Math.min(0, v))

  /** 绑定某一行的触摸事件处理器 */
  const bindRow = (rowId: string | number) => ({
    onTouchstart: (e: TouchEvent) => {
      // 起手另一行时收起已展开的行
      if (openRowId.value !== null && openRowId.value !== rowId) {
        closeRow()
      }
      activeRowId.value = rowId
      aborted = false
      startX = e.touches[0].clientX
      startY = e.touches[0].clientY
      baseOffset = openRowId.value === rowId ? -threshold : 0
    },

    onTouchmove: (e: TouchEvent) => {
      if (activeRowId.value !== rowId || aborted) return
      const deltaX = e.touches[0].clientX - startX
      const deltaY = e.touches[0].clientY - startY
      // 垂直主导的手势交给滚动，忽略本次滑动并回到基线
      if (Math.abs(deltaY) > Math.abs(deltaX)) {
        aborted = true
        rowOffset.value = baseOffset
        return
      }
      rowOffset.value = clamp(baseOffset + deltaX)
    },

    onTouchend: () => {
      if (activeRowId.value !== rowId) return
      activeRowId.value = null
      if (aborted) {
        aborted = false
        rowOffset.value = openRowId.value === rowId ? -threshold : 0
        return
      }
      // 过半阈值驻留展开，否则回弹收起（已展开行右滑过半即关闭）
      if (rowOffset.value < -threshold / 2) {
        openRowId.value = rowId
        rowOffset.value = -threshold
      } else {
        if (openRowId.value === rowId) openRowId.value = null
        rowOffset.value = 0
      }
    },
  })

  return {
    bindRow,
    openRowId: readonly(openRowId),
    activeRowId: readonly(activeRowId),
    rowOffset: readonly(rowOffset),
    closeRow,
  }
}
