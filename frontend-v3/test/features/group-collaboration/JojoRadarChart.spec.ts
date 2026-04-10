import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import JojoRadarChart from '@/features/group-collaboration/components/JojoRadarChart.vue'

describe('JojoRadarChart', () => {
  it('renders chart container', () => {
    const wrapper = mount(JojoRadarChart, {
      props: {
        dimensions: ['创意', '执行力'],
        teacherScores: [80, 90],
        peerScores: [70, 85],
      },
    })
    expect(wrapper.find('div').exists()).toBe(true)
  })
})
