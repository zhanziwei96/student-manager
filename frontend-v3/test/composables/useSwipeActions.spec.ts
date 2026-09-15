/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from 'vitest'
import { useSwipeActions } from '@/composables/useSwipeActions'

/**
 * useSwipeActions composable 测试
 * 验证行左滑展开、单展开互斥、基线偏移、clamp 与收起
 */

// jsdom 不支持 TouchEvent 构造器，用 Event + 补丁模拟触摸事件
function makeTouchEvent(type: string, x: number, y: number): TouchEvent {
  const touch = { clientX: x, clientY: y, identifier: 0 }
  return Object.assign(new Event(type, { bubbles: true, cancelable: true }), {
    touches: type === 'touchend' ? [] : [touch],
    changedTouches: [touch],
  }) as unknown as TouchEvent
}

/** 展开一行的便捷方法（左滑 100px 后松手） */
function openRow(row: ReturnType<ReturnType<typeof useSwipeActions>['bindRow']>) {
  row.onTouchstart(makeTouchEvent('touchstart', 300, 100))
  row.onTouchmove(makeTouchEvent('touchmove', 200, 100))
  row.onTouchend(makeTouchEvent('touchend', 200, 100))
}

describe('useSwipeActions', () => {
  it('左滑超过阈值后驻留展开', () => {
    const { bindRow, openRowId, rowOffset } = useSwipeActions()
    const row = bindRow('r1')

    row.onTouchstart(makeTouchEvent('touchstart', 300, 100))
    row.onTouchmove(makeTouchEvent('touchmove', 200, 100))
    // 跟手位移，clamp 到 -96（默认阈值 64 * 1.5）
    expect(rowOffset.value).toBe(-96)

    row.onTouchend(makeTouchEvent('touchend', 200, 100))
    expect(openRowId.value).toBe('r1')
    // 驻留在阈值宽度
    expect(rowOffset.value).toBe(-64)
  })

  it('手势进行中暴露 activeRowId，松手后归 null', () => {
    const { bindRow, activeRowId } = useSwipeActions()
    const row = bindRow('r1')

    expect(activeRowId.value).toBeNull()
    row.onTouchstart(makeTouchEvent('touchstart', 300, 100))
    expect(activeRowId.value).toBe('r1')
    row.onTouchmove(makeTouchEvent('touchmove', 200, 100))
    row.onTouchend(makeTouchEvent('touchend', 200, 100))
    expect(activeRowId.value).toBeNull()
  })

  it('已展开行轻微左滑不收起（基线从 -threshold 起算）', () => {
    const { bindRow, openRowId, rowOffset } = useSwipeActions()
    const row = bindRow('r1')
    openRow(row)
    expect(openRowId.value).toBe('r1')

    // 再触摸并左滑 5px：offset 从 -64 平滑到 -69，不跳变
    row.onTouchstart(makeTouchEvent('touchstart', 300, 100))
    row.onTouchmove(makeTouchEvent('touchmove', 295, 100))
    expect(rowOffset.value).toBe(-69)

    row.onTouchend(makeTouchEvent('touchend', 295, 100))
    expect(openRowId.value).toBe('r1')
    expect(rowOffset.value).toBe(-64)
  })

  it('已展开行右滑过半后收起', () => {
    const { bindRow, openRowId, rowOffset } = useSwipeActions()
    const row = bindRow('r1')
    openRow(row)

    // 右滑 40px：offset = -64 + 40 = -24 > -32（半阈值），收起
    row.onTouchstart(makeTouchEvent('touchstart', 300, 100))
    row.onTouchmove(makeTouchEvent('touchmove', 340, 100))
    row.onTouchend(makeTouchEvent('touchend', 340, 100))

    expect(openRowId.value).toBeNull()
    expect(rowOffset.value).toBe(0)
  })

  it('快速长滑时位移 clamp 到上限（不超过阈值 1.5 倍）', () => {
    const { bindRow, rowOffset } = useSwipeActions()
    const row = bindRow('r1')

    row.onTouchstart(makeTouchEvent('touchstart', 600, 100))
    row.onTouchmove(makeTouchEvent('touchmove', 100, 100))
    expect(rowOffset.value).toBe(-96)
  })

  it('左滑未达半阈值时回弹收起', () => {
    const { bindRow, openRowId, rowOffset } = useSwipeActions()
    const row = bindRow('r1')

    row.onTouchstart(makeTouchEvent('touchstart', 300, 100))
    row.onTouchmove(makeTouchEvent('touchmove', 280, 100))
    row.onTouchend(makeTouchEvent('touchend', 280, 100))

    expect(openRowId.value).toBeNull()
    expect(rowOffset.value).toBe(0)
  })

  it('滑动另一行时收起已展开的行', () => {
    const { bindRow, openRowId, rowOffset } = useSwipeActions()
    const row1 = bindRow('r1')
    const row2 = bindRow('r2')

    openRow(row1)
    expect(openRowId.value).toBe('r1')

    // 起手 r2 即收起 r1
    row2.onTouchstart(makeTouchEvent('touchstart', 300, 200))
    expect(openRowId.value).toBeNull()
    expect(rowOffset.value).toBe(0)
  })

  it('closeRow 收起当前展开的行', () => {
    const { bindRow, openRowId, rowOffset, closeRow } = useSwipeActions()
    const row = bindRow('r1')
    openRow(row)
    expect(openRowId.value).toBe('r1')

    closeRow()
    expect(openRowId.value).toBeNull()
    expect(rowOffset.value).toBe(0)
  })

  it('垂直主导的手势被忽略并回到基线', () => {
    const { bindRow, openRowId, rowOffset } = useSwipeActions()
    const row = bindRow('r1')

    row.onTouchstart(makeTouchEvent('touchstart', 300, 100))
    row.onTouchmove(makeTouchEvent('touchmove', 260, 160))
    row.onTouchend(makeTouchEvent('touchend', 260, 160))

    expect(openRowId.value).toBeNull()
    expect(rowOffset.value).toBe(0)
  })
})
