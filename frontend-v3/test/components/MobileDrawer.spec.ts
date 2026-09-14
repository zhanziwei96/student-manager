/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import MobileDrawer from '@/components/ui/MobileDrawer.vue'

// 可变的角色/路由状态（vi.mock 工厂内只能引用 hoisted 变量）
const mockState = vi.hoisted(() => ({
  role: 'teacher' as 'admin' | 'teacher' | 'student',
  path: '/teacher',
  logout: vi.fn()
}))

vi.mock('vue-router', async () => {
  const { defineComponent, h } = await import('vue')
  return {
    useRoute: () => ({ path: mockState.path }),
    // 轻量 RouterLink stub：渲染为 <a href="...">
    RouterLink: defineComponent({
      name: 'RouterLink',
      props: { to: { type: [String, Object], required: true } },
      setup(props, { slots }) {
        return () => h('a', { href: String(props.to) }, slots.default?.())
      }
    })
  }
})

vi.mock('@/stores', () => ({
  useAuthStore: () => ({
    get user() {
      return { name: '测试用户', role: mockState.role }
    },
    get isAdmin() {
      return mockState.role === 'admin'
    },
    logout: mockState.logout
  })
}))

const mountDrawer = () =>
  mount(MobileDrawer, { props: { open: true } })

describe('MobileDrawer（收窄为「我的」账户面板）', () => {
  beforeEach(() => {
    mockState.logout.mockReset()
    mockState.logout.mockResolvedValue(undefined)
  })

  it('教师：无导航链接，仅保留修改密码/退出登录，标题为「我的」', () => {
    mockState.role = 'teacher'
    mockState.path = '/teacher'
    const wrapper = mountDrawer()

    // 无任何导航链接
    expect(wrapper.findAll('a').length).toBe(0)
    const text = wrapper.text()
    expect(text).not.toContain('仪表板')
    expect(text).not.toContain('课堂签到')

    // 账户面板内容保留
    expect(text).toContain('我的')
    expect(text).toContain('修改密码')
    expect(text).toContain('退出登录')
    expect(text).toContain('测试用户')
  })

  it('学生：无导航链接，仅保留修改密码/退出登录', () => {
    mockState.role = 'student'
    mockState.path = '/student'
    const wrapper = mountDrawer()

    expect(wrapper.findAll('a').length).toBe(0)
    const text = wrapper.text()
    expect(text).not.toContain('仪表板')
    expect(text).not.toContain('我的成绩')
    expect(text).toContain('修改密码')
    expect(text).toContain('退出登录')
  })

  it('管理员：仍保留导航链接（无 BottomNav）', () => {
    mockState.role = 'admin'
    mockState.path = '/admin'
    const wrapper = mountDrawer()

    const links = wrapper.findAll('a')
    expect(links.length).toBeGreaterThan(0)
    const hrefs = links.map((a) => a.attributes('href'))
    expect(hrefs).toContain('/admin')
    expect(hrefs).toContain('/admin/semesters')
    expect(hrefs).toContain('/admin/students')
    expect(hrefs).toContain('/admin/checkins')
  })

  it('点击「修改密码」emit changePassword 并关闭抽屉', async () => {
    mockState.role = 'teacher'
    mockState.path = '/teacher'
    const wrapper = mountDrawer()

    const btn = wrapper.findAll('button').find((b) => b.text().includes('修改密码'))
    expect(btn).toBeTruthy()
    await btn!.trigger('click')

    expect(wrapper.emitted('changePassword')).toHaveLength(1)
    expect(wrapper.emitted('update:open')).toEqual([[false]])
  })

  it('点击「退出登录」调用 store.logout 并关闭抽屉', async () => {
    mockState.role = 'teacher'
    mockState.path = '/teacher'
    const wrapper = mountDrawer()

    const btn = wrapper.findAll('button').find((b) => b.text().includes('退出登录'))
    expect(btn).toBeTruthy()
    await btn!.trigger('click')
    await flushPromises()

    expect(mockState.logout).toHaveBeenCalledTimes(1)
    expect(wrapper.emitted('update:open')).toEqual([[false]])
  })
})
