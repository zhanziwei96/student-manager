/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from 'vitest'
import { useSwipeActions } from '@/composables/useSwipeActions'

/**
 * useSwipeActions composable 测试
 * 验证行左滑展开、单展开互斥与收起
 */

// jsdom 不支持 TouchEvent 构造器，用 Event + 补丁模拟触摸事件
function makeTouchEvent(type: string, x: number, y: number): TouchEvent {
  const touch = { clientX: x, clientY: y, identifier: 0 }
  return Object.assign(new Event(type, { bubbles: true, cancelable: true }), {
    touches: type === 'touchend' ? [] : [touch],
    changedTouches: [touch],
  }) as unknown as TouchEvent
}

describe('useSwipeActions', () => {
  it('左滑超过阈值后驻留展开', () => {
    const { bindRow, openRowId, rowOffset } = useSwipeActions()
    const row = bindRow('r1')

    row.onTouchstart(makeTouchEvent('touchstart', 300, 100))
    row.onTouchmove(makeTouchEvent('touchmove', 200, 100))
    // 跟手位移
    expect(rowOffset.value).toBe(-100)

    row.onTouchend(makeTouchEvent('touchend', 200, 100))
    expect(openRowId.value).toBe('r1')
    // 驻留在阈值宽度
    expect(rowOffset.value).toBe(-64)
  })

  it('左滑未达阈值时回弹收起', () => {
    const { bindRow, openRowId, rowOffset } = useSwipeActions()
    const row = bindRow('r1')

    row.onTouchstart(makeTouchEvent('touchstart', 300, 100))
    row.onTouchmove(makeTouchEvent('touchmove', 270, 100))
    row.onTouchend(makeTouchEvent('touchend', 270, 100))

    expect(openRowId.value).toBeNull()
    expect(rowOffset.value).toBe(0)
  })

  it('滑动另一行时收起已展开的行', () => {
    const { bindRow, openRowId, rowOffset } = useSwipeActions()
    const row1 = bindRow('r1')
    const row2 = bindRow('r2')

    // 先展开 r1
    row1.onTouchstart(makeTouchEvent('touchstart', 300, 100))
    row1.onTouchmove(makeTouchEvent('touchmove', 200, 100))
    row1.onTouchend(makeTouchEvent('touchend', 200, 100))
    expect(openRowId.value).toBe('r1')

    // 起手 r2 即收起 r1
    row2.onTouchstart(makeTouchEvent('touchstart', 300, 200))
    expect(openRowId.value).toBeNull()
    expect(rowOffset.value).toBe(0)
  })

  it('closeRow 收起当前展开的行', () => {
    const { bindRow, openRowId, rowOffset, closeRow } = useSwipeActions()
    const row = bindRow('r1')

    row.onTouchstart(makeTouchEvent('touchstart', 300, 100))
    row.onTouchmove(makeTouchEvent('touchmove', 200, 100))
    row.onTouchend(makeTouchEvent('touchend', 200, 100))
    expect(openRowId.value).toBe('r1')

    closeRow()
    expect(openRowId.value).toBeNull()
    expect(rowOffset.value).toBe(0)
  })

  it('垂直主导的手势被忽略', () => {
    const { bindRow, openRowId, rowOffset } = useSwipeActions()
    const row = bindRow('r1')

    row.onTouchstart(makeTouchEvent('touchstart', 300, 100))
    row.onTouchmove(makeTouchEvent('touchmove', 260, 160))
    row.onTouchend(makeTouchEvent('touchend', 260, 160))

    expect(openRowId.value).toBeNull()
    expect(rowOffset.value).toBe(0)
  })
})
