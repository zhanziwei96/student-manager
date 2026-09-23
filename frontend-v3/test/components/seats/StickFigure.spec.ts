/** @vitest-environment jsdom */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StickFigure from '@/components/seats/StickFigure.vue'

describe('StickFigure', () => {
  it('渲染 svg 且 data-pose 跟随 prop', () => {
    const wrapper = mount(StickFigure, { props: { pose: 'walk' } })
    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.attributes('data-pose')).toBe('walk')
  })

  it('六个姿势都合法', () => {
    for (const pose of ['stand', 'walk', 'carry', 'sit', 'scratch', 'cheer'] as const) {
      const wrapper = mount(StickFigure, { props: { pose } })
      expect(wrapper.find('svg').exists()).toBe(true)
    }
  })

  it('头部始终是圆形（圆头设定）', () => {
    const wrapper = mount(StickFigure, { props: { pose: 'sit' } })
    expect(wrapper.find('circle.stick-head').exists()).toBe(true)
  })
})
