/** @vitest-environment jsdom */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SeatUnit from '@/components/seats/SeatUnit.vue'
import type { SeatCell } from '@/types/seats'

const cell = (over: Partial<SeatCell> = {}): SeatCell => ({
  seat_id: 1, seat_no: 'P11', row: 1, col: 1, is_broken: false,
  state: 'empty', student_id: null, student_name: null, ...over,
})

describe('SeatUnit', () => {
  it('空位显示座位编号', () => {
    const wrapper = mount(SeatUnit, { props: { seat: cell(), selectable: true } })
    expect(wrapper.text()).toContain('P11')
    expect(wrapper.attributes('data-state')).toBe('empty')
  })

  it('已占显示姓名', () => {
    const wrapper = mount(SeatUnit, {
      props: { seat: cell({ state: 'occupied', student_name: '张三' }), selectable: false },
    })
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).not.toContain('P11')
  })

  it('故障座位不可点', async () => {
    const wrapper = mount(SeatUnit, {
      props: { seat: cell({ is_broken: true }), selectable: true },
    })
    expect(wrapper.attributes('data-broken')).toBe('true')
    expect(wrapper.attributes('aria-disabled')).toBe('true')
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeUndefined()
  })

  it('可点的空位触发 click', async () => {
    const wrapper = mount(SeatUnit, { props: { seat: cell(), selectable: true } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('我的座位有 mine 态', () => {
    const wrapper = mount(SeatUnit, {
      props: { seat: cell({ state: 'mine', student_name: '我' }), selectable: true },
    })
    expect(wrapper.attributes('data-state')).toBe('mine')
  })
})
