/** @vitest-environment jsdom */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SeatMap from '@/components/seats/SeatMap.vue'
import type { ClassroomInfo, SeatCell } from '@/types/seats'

const classroom: ClassroomInfo = {
  id: 1, name: '机房302', rows: 2, cols: 4, status: 'active', seat_count: 8,
}
const seats: SeatCell[] = Array.from({ length: 8 }, (_, i) => ({
  seat_id: i + 1, seat_no: `P${Math.floor(i / 4) + 1}${(i % 4) + 1}`,
  row: Math.floor(i / 4) + 1, col: (i % 4) + 1,
  is_broken: false, state: 'empty', student_id: null, student_name: null,
}))

describe('SeatMap', () => {
  it('按 rows×cols 渲染全部座位', () => {
    const wrapper = mount(SeatMap, {
      props: { classroom, seats, mode: 'student' },
    })
    expect(wrapper.findAll('.seat-unit')).toHaveLength(8)
  })

  it('有讲台与两个门标记', () => {
    const wrapper = mount(SeatMap, {
      props: { classroom, seats, mode: 'student' },
    })
    expect(wrapper.find('.seat-podium').exists()).toBe(true)
    expect(wrapper.findAll('.seat-door')).toHaveLength(2)
  })

  it('学生模式点空位发出 seat-click', async () => {
    const wrapper = mount(SeatMap, {
      props: { classroom, seats, mode: 'student' },
    })
    await wrapper.findAll('.seat-unit')[0].trigger('click')
    expect(wrapper.emitted('seat-click')?.[0][0]).toMatchObject({ seat_no: 'P11' })
  })

  it('深色作用域类存在', () => {
    const wrapper = mount(SeatMap, {
      props: { classroom, seats, mode: 'teacher' },
    })
    expect(wrapper.find('.seat-map-dark').exists()).toBe(true)
  })
})
