import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import JojoRadarChart from '@/features/group-collaboration/components/JojoRadarChart.vue'

describe('JojoRadarChart', () => {
  it('renders canvas container with dimensions and finalScores', () => {
    const wrapper = mount(JojoRadarChart, {
      props: {
        dimensions: ['创意', '执行力'],
        finalScores: [80, 90],
        groupName: '测试组',
      },
    })
    expect(wrapper.find('canvas').exists()).toBe(true)
    expect(wrapper.find('.jojo-radar-chart').exists()).toBe(true)
  })

  it('renders with six dimensions', () => {
    const wrapper = mount(JojoRadarChart, {
      props: {
        dimensions: ['破坏力', '速度', '射程距离', '持续力', '精密动作性', '成长性'],
        finalScores: [80, 100, 40, 80, 100, 60],
        groupName: '替身小组',
      },
    })
    expect(wrapper.find('canvas').exists()).toBe(true)
  })
})
