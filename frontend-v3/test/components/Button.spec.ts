/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from '@/components/ui/Button.vue'

describe('Button', () => {
  it('所有尺寸触控热区不低于 44px（HIG 下限）', () => {
    const sizes = ['sm', 'default', 'lg', 'icon'] as const
    for (const size of sizes) {
      const wrapper = mount(Button, { props: { size } })
      expect(wrapper.classes()).toContain('min-h-[44px]')
    }
  })

  it('icon 尺寸同时保证最小宽度 44px', () => {
    const wrapper = mount(Button, { props: { size: 'icon' } })
    expect(wrapper.classes()).toContain('min-w-[44px]')
  })
})
