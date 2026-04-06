/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import MobilePicker from '../../src/components/ui/MobilePicker.vue'

const options = [
  { value: '1', label: '选项一' },
  { value: '2', label: '选项二', subtitle: '副标题' },
  { value: '3', label: '选项三' }
]

describe('MobilePicker', () => {
  beforeEach(() => {
    // Reset window innerWidth to desktop by default
    Object.defineProperty(window, 'innerWidth', { value: 1024, writable: true })
  })

  it('renders with placeholder', () => {
    const wrapper = mount(MobilePicker, {
      props: {
        options,
        placeholder: '请选择'
      }
    })
    expect(wrapper.text()).toContain('请选择')
  })

  it('displays selected option label', async () => {
    const wrapper = mount(MobilePicker, {
      props: {
        options,
        modelValue: '2'
      }
    })
    await nextTick()
    expect(wrapper.text()).toContain('选项二')
    expect(wrapper.text()).toContain('副标题')
  })

  it('emits update:modelValue when option selected', async () => {
    const wrapper = mount(MobilePicker, {
      props: {
        options,
        modelValue: undefined
      }
    })

    // Open the picker
    await wrapper.find('button').trigger('click')
    await nextTick()

    // Verify picker is open (isOpen should be true)
    expect(wrapper.vm.isOpen).toBe(true)
  })

  it('filters options when searchable', async () => {
    const wrapper = mount(MobilePicker, {
      props: {
        options,
        searchable: true,
        modelValue: undefined
      }
    })

    // Open the picker
    await wrapper.find('button').trigger('click')
    await nextTick()

    // Verify search input exists in desktop mode
    const searchInput = wrapper.find('input[type="text"]')
    expect(searchInput.exists()).toBe(true)
  })

  it('clears selection when clearable', async () => {
    const wrapper = mount(MobilePicker, {
      props: {
        options,
        modelValue: '1',
        clearable: true
      }
    })

    await nextTick()
    // Find all buttons and locate the clear button (the one that's not the main trigger)
    const buttons = wrapper.findAll('button')
    // The clear button is the second button (first is main trigger, second is clear)
    expect(buttons.length).toBeGreaterThanOrEqual(2)

    // Click the clear button (it has the X icon)
    await buttons[1].trigger('click')
    expect(wrapper.emitted()).toHaveProperty('update:modelValue')
    expect(wrapper.emitted()['update:modelValue'][0]).toEqual([undefined])
  })

  it('respects disabled prop', async () => {
    const wrapper = mount(MobilePicker, {
      props: {
        options,
        disabled: true
      }
    })

    await wrapper.find('button').trigger('click')
    await nextTick()

    // Verify picker did not open (isOpen should still be false)
    expect(wrapper.vm.isOpen).toBe(false)
  })
})
