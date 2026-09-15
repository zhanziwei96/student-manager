/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from '@/components/ui/Button.vue'

describe('Button', () => {
  it('所有尺寸移动端触控热区不低于 44px（HIG 下限；桌面端保持原尺寸）', () => {
    const sizes = ['sm', 'default', 'lg', 'icon'] as const
    for (const size of sizes) {
      const wrapper = mount(Button, { props: { size } })
      expect(wrapper.classes()).toContain('max-md:min-h-[44px]')
    }
  })

  it('icon 尺寸移动端同时保证最小宽度 44px', () => {
    const wrapper = mount(Button, { props: { size: 'icon' } })
    expect(wrapper.classes()).toContain('max-md:min-w-[44px]')
  })

  it('桌面端保持原有固定高度（不带断点的 h-* 保留）', () => {
    const wrapper = mount(Button, { props: { size: 'sm' } })
    expect(wrapper.classes()).toContain('h-8')
    expect(wrapper.classes()).not.toContain('min-h-[44px]') // 不带断点前缀的全局 min-h 不得存在
  })
})
