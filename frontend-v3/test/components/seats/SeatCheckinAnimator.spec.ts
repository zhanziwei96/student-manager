/** @vitest-environment jsdom */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SeatCheckinAnimator from '@/components/seats/SeatCheckinAnimator.vue'

describe('SeatCheckinAnimator', () => {
  it('idle 时不渲染火柴人', () => {
    const wrapper = mount(SeatCheckinAnimator, { props: { state: 'idle' } })
    expect(wrapper.find('[data-pose]').exists()).toBe(false)
  })

  it('walking → 火柴人进入', () => {
    const wrapper = mount(SeatCheckinAnimator, { props: { state: 'walking' } })
    expect(wrapper.find('[data-pose="walk"]').exists()).toBe(true)
  })

  it('success 动画播完发出 finished', async () => {
    vi.useFakeTimers()
    const wrapper = mount(SeatCheckinAnimator, { props: { state: 'success' } })
    await vi.runAllTimersAsync()
    expect(wrapper.emitted('finished')).toHaveLength(1)
    vi.useRealTimers()
  })

  it('fail 播挠头姿势', () => {
    const wrapper = mount(SeatCheckinAnimator, { props: { state: 'fail' } })
    expect(wrapper.find('[data-pose="scratch"]').exists()).toBe(true)
  })
})
