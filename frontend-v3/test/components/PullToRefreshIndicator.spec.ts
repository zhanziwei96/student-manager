/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PullToRefreshIndicator from '@/components/ui/PullToRefreshIndicator.vue'

describe('PullToRefreshIndicator', () => {
  it('未下拉且不刷新时不渲染', () => {
    const wrapper = mount(PullToRefreshIndicator, {
      props: { pulling: false, pullDistance: 0, refreshing: false },
    })
    expect(wrapper.html()).toBe('<!--v-if-->')
  })

  it('下拉未达阈值显示「下拉刷新」', () => {
    const wrapper = mount(PullToRefreshIndicator, {
      props: { pulling: true, pullDistance: 40, refreshing: false },
    })
    expect(wrapper.text()).toContain('下拉刷新')
    expect(wrapper.text()).not.toContain('释放刷新')
  })

  it('下拉达到阈值显示「释放刷新」', () => {
    const wrapper = mount(PullToRefreshIndicator, {
      props: { pulling: true, pullDistance: 90, refreshing: false },
    })
    expect(wrapper.text()).toContain('释放刷新')
  })

  it('刷新中显示「刷新中…」', () => {
    const wrapper = mount(PullToRefreshIndicator, {
      props: { pulling: false, pullDistance: 80, refreshing: true },
    })
    expect(wrapper.text()).toContain('刷新中…')
  })

  it('高度跟随下拉距离', () => {
    const wrapper = mount(PullToRefreshIndicator, {
      props: { pulling: true, pullDistance: 66, refreshing: false },
    })
    expect(wrapper.attributes('style')).toContain('height: 66px')
  })
})
