/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import BottomNav from '@/components/ui/BottomNav.vue'

// 可变的角色/路由状态（vi.mock 工厂内只能引用 hoisted 变量）
const mockState = vi.hoisted(() => ({
  role: 'teacher' as 'teacher' | 'student',
  path: '/teacher',
  logout: vi.fn()
}))

vi.mock('vue-router', async () => {
  const { defineComponent, h } = await import('vue')
  return {
    useRoute: () => ({ path: mockState.path }),
    // 轻量 RouterLink stub：渲染为 <a href="...">，class 透传合并
    RouterLink: defineComponent({
      name: 'RouterLink',
      props: { to: { type: [String, Object], required: true } },
      setup(props, { slots }) {
        return () => h('a', { href: String(props.to) }, slots.default?.())
      }
    })
  }
})

// Mock stores（沿用 CourseSession.spec.ts 的 vi.mock('@/stores') 模式）
vi.mock('@/stores', () => ({
  useAuthStore: () => ({
    get isTeacher() {
      return mockState.role === 'teacher'
    },
    get isStudent() {
      return mockState.role === 'student'
    },
    logout: mockState.logout
  })
}))

const mountNav = () =>
  mount(BottomNav, { attachTo: document.body })

/** 打开「更多」面板 */
const openMore = async (wrapper: ReturnType<typeof mountNav>) => {
  const moreBtn = wrapper.findAll('button').find((b) => b.text().includes('更多'))
  expect(moreBtn).toBeTruthy()
  await moreBtn!.trigger('click')
  await flushPromises()
}

describe('BottomNav', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    mockState.logout.mockClear()
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('教师端：仪表板/学生/课表/更多 + 中央签到按钮', () => {
    mockState.role = 'teacher'
    mockState.path = '/teacher'
    const wrapper = mountNav()

    const text = wrapper.text()
    expect(text).toContain('仪表板')
    expect(text).toContain('学生')
    expect(text).toContain('课表')
    expect(text).toContain('更多')

    const checkin = wrapper.find('a[aria-label="签到"]')
    expect(checkin.exists()).toBe(true)
    expect(checkin.attributes('href')).toBe('/teacher/session')
    expect(checkin.classes()).toContain('bg-black')
    expect(checkin.classes()).toContain('rounded-full')

    wrapper.unmount()
  })

  it('学生端：仪表板/小组/成绩/更多 + 中央签到按钮', () => {
    mockState.role = 'student'
    mockState.path = '/student'
    const wrapper = mountNav()

    const text = wrapper.text()
    expect(text).toContain('仪表板')
    expect(text).toContain('小组')
    expect(text).toContain('成绩')
    expect(text).toContain('更多')

    const checkin = wrapper.find('a[aria-label="签到"]')
    expect(checkin.attributes('href')).toBe('/student/checkin')

    wrapper.unmount()
  })

  it('不渲染死链路由（group-tasks/group-evaluations/group-results）', () => {
    mockState.role = 'teacher'
    mockState.path = '/teacher'
    const wrapper = mountNav()

    expect(wrapper.html()).not.toContain('group-tasks')
    expect(wrapper.html()).not.toContain('group-evaluations')
    expect(wrapper.html()).not.toContain('group-results')

    wrapper.unmount()
  })

  it('点击「更多」打开 BottomSheet', async () => {
    mockState.role = 'teacher'
    mockState.path = '/teacher'
    const wrapper = mountNav()

    expect(document.body.querySelector('[role="dialog"]')).toBeNull()

    await openMore(wrapper)

    expect(document.body.querySelector('[role="dialog"]')).toBeTruthy()

    wrapper.unmount()
  })

  it('教师端面板：列出剩余入口 + 账号操作', async () => {
    mockState.role = 'teacher'
    mockState.path = '/teacher'
    const wrapper = mountNav()
    await openMore(wrapper)

    const sheet = document.body.querySelector('[role="dialog"]')!
    expect(sheet.textContent).toContain('我的教学班')
    expect(sheet.textContent).toContain('小组管理')
    expect(sheet.textContent).toContain('课堂问答')
    expect(sheet.textContent).toContain('排行榜')
    expect(sheet.textContent).toContain('历史课堂')
    expect(sheet.textContent).toContain('失物招领')
    expect(sheet.textContent).toContain('修改密码')
    expect(sheet.textContent).toContain('退出登录')

    expect(sheet.querySelector('a[href="/teacher/my-offerings"]')).toBeTruthy()
    expect(sheet.querySelector('a[href="/teacher/groups"]')).toBeTruthy()
    expect(sheet.querySelector('a[href="/teacher/sessions-history"]')).toBeTruthy()

    wrapper.unmount()
  })

  it('学生端面板：仅问答/排行榜/失物招领 + 账号操作', async () => {
    mockState.role = 'student'
    mockState.path = '/student'
    const wrapper = mountNav()
    await openMore(wrapper)

    const sheet = document.body.querySelector('[role="dialog"]')!
    expect(sheet.textContent).toContain('课堂问答')
    expect(sheet.textContent).toContain('排行榜')
    expect(sheet.textContent).toContain('失物招领')
    expect(sheet.textContent).toContain('修改密码')
    expect(sheet.textContent).toContain('退出登录')
    expect(sheet.textContent).not.toContain('我的教学班')
    expect(sheet.textContent).not.toContain('历史课堂')

    wrapper.unmount()
  })

  it('当前路由属于「更多」条目时，更多 tab 呈选中态', () => {
    mockState.role = 'teacher'
    mockState.path = '/teacher/groups'
    const wrapper = mountNav()

    const moreBtn = wrapper.findAll('button').find((b) => b.text().includes('更多'))!
    expect(moreBtn.classes()).toContain('text-black')
    expect(moreBtn.classes()).toContain('font-medium')

    wrapper.unmount()
  })

  it('「修改密码」向上 emit changePassword 并关闭面板', async () => {
    mockState.role = 'teacher'
    mockState.path = '/teacher'
    const wrapper = mountNav()
    await openMore(wrapper)

    const pwdBtn = Array.from(
      document.body.querySelectorAll('[role="dialog"] button')
    ).find((b) => b.textContent?.includes('修改密码')) as HTMLElement
    pwdBtn.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()

    expect(wrapper.emitted('changePassword')).toBeTruthy()
    expect(document.body.querySelector('[role="dialog"]')).toBeNull()

    wrapper.unmount()
  })

  it('「退出登录」调用 authStore.logout 并关闭面板', async () => {
    mockState.role = 'teacher'
    mockState.path = '/teacher'
    const wrapper = mountNav()
    await openMore(wrapper)

    const logoutBtn = Array.from(
      document.body.querySelectorAll('[role="dialog"] button')
    ).find((b) => b.textContent?.includes('退出登录')) as HTMLElement
    logoutBtn.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()

    expect(mockState.logout).toHaveBeenCalled()
    expect(document.body.querySelector('[role="dialog"]')).toBeNull()

    wrapper.unmount()
  })
})
