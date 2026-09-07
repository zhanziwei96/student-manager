/**
 * @vitest-environment jsdom
 *
 * 科目管理页（实现位于 teacher 视图，admin 路由复用）- 科目列表渲染测试
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Subjects from '@/views/teacher/Subjects.vue'

// Mock composables
vi.mock('@/composables/useSubjects', () => ({
  useSubjects: vi.fn(() => ({
    data: { value: [{ id: 1, name: '数学', semester: '2026-2027-1' }] },
    isPending: { value: false },
  })),
  useUpdateSubject: vi.fn(() => ({ mutateAsync: vi.fn() })),
  useDeriveSubjects: vi.fn(() => ({ mutateAsync: vi.fn() })),
}))

describe('Subjects', () => {
  it('renders subject list', () => {
    const wrapper = mount(Subjects)
    expect(wrapper.text()).toContain('数学')
  })
})
