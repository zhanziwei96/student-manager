/**
 * @vitest-environment jsdom
 *
 * 复现：学生签到页轮询导致输入验证码时丢失光标
 *
 * 刻意只在 HTTP 边界（@/lib/api）做 mock，让 composable / queryKey /
 * refetchInterval 全部走真实逻辑——否则 mock 掉 useQuery 就复现不出问题。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'

const get = vi.fn()

vi.mock('@/lib/api', () => ({
  get: (url: string) => get(url),
  post: vi.fn(),
  put: vi.fn(),
  patch: vi.fn(),
  del: vi.fn(),
  api: {},
  ApiError: class ApiError extends Error {},
  requestRaw: vi.fn(),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  toast: { success: vi.fn(), error: vi.fn() },
}))

import StudentCheckin from '@/views/student/Checkin.vue'

const STUDENT = { id: 1, username: 'S001', name: '张三', role: 'student' }
const PROFILE = { student_id: 'S001', name: '张三', class_id: 5, class_name: '2026届计算机1班' }
const SESSION = {
  id: 42, session_code: 'ABCDEF', active: true,
  course_name: '高等数学', class_name: '2026届计算机1班',
  teacher_name: '李老师', start_time: '2026-09-21T08:00:00',
}

function makeClient() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { staleTime: 1000 * 60 * 5, refetchOnWindowFocus: true, retry: false },
    },
  })
  // 模拟路由守卫已拉过 /me
  client.setQueryData(['me'], STUDENT)
  return client
}

const host = document.createElement('div')

function mountPage() {
  const queryClient = makeClient()
  // 必须 attachTo 真实文档，否则 focus() 不生效、document.activeElement 永远是 body
  return mount(StudentCheckin, {
    attachTo: host,
    global: { plugins: [[VueQueryPlugin, { queryClient }]] },
  })
}

describe('学生签到页轮询与光标', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    document.body.appendChild(host)
    get.mockReset()
    get.mockImplementation((url: string) => {
      if (url === '/me') return Promise.resolve(STUDENT)
      if (url.startsWith('/students/')) return Promise.resolve(PROFILE)
      if (url.startsWith('/course-sessions/class/')) return Promise.resolve(SESSION)
      if (url.startsWith('/checkins/session/')) return Promise.resolve([])
      if (url.startsWith('/checkins/stats')) {
        return Promise.resolve({
          active: true, class_name: '2026届计算机1班',
          total: 30, checked_in: 0, not_checked_in: 30, rate: 0,
        })
      }
      return Promise.resolve(null)
    })
  })

  afterEach(() => {
    host.innerHTML = ''
    if (host.parentNode) host.parentNode.removeChild(host)
    vi.useRealTimers()
  })

  async function settle(times = 6) {
    for (let i = 0; i < times; i++) {
      await vi.advanceTimersByTimeAsync(0)
      await flushPromises()
    }
  }

  it('验证码输入框在轮询刷新后仍然保留 DOM 节点与焦点', async () => {
    const wrapper = mountPage()
    await settle()

    const input = wrapper.find('input')
    expect(input.exists(), '验证码输入框应已渲染').toBe(true)

    const inputEl = input.element as HTMLInputElement
    inputEl.focus()
    expect(document.activeElement).toBe(inputEl)

    // 推进 35 秒，覆盖 ['student-course-session'] / ['session-checkins'] 的 10s 轮询
    for (let i = 0; i < 4; i++) {
      await vi.advanceTimersByTimeAsync(10000)
      await flushPromises()
    }

    expect(wrapper.find('input').element, '输入框 DOM 节点不应被替换').toBe(inputEl)
    expect(document.activeElement, '输入框焦点不应丢失').toBe(inputEl)
  })

  it('后台轮询失败不得卸载验证码输入框（否则学生打验证码时丢光标）', async () => {
    let sessionCalls = 0
    get.mockImplementation((url: string) => {
      if (url === '/me') return Promise.resolve(STUDENT)
      if (url.startsWith('/students/')) return Promise.resolve(PROFILE)
      if (url.startsWith('/course-sessions/class/')) {
        sessionCalls += 1
        // 首次成功，之后每次轮询都失败（模拟后端 429/500/网络抖动）
        return sessionCalls === 1
          ? Promise.resolve(SESSION)
          : Promise.reject(new Error('请求过于频繁，请稍后再试'))
      }
      if (url.startsWith('/checkins/session/')) return Promise.resolve([])
      if (url.startsWith('/checkins/stats')) {
        return Promise.resolve({
          active: true, class_name: '2026届计算机1班',
          total: 30, checked_in: 0, not_checked_in: 30, rate: 0,
        })
      }
      return Promise.resolve(null)
    })

    const wrapper = mountPage()
    await settle()

    const input = wrapper.find('input')
    expect(input.exists()).toBe(true)
    const inputEl = input.element as HTMLInputElement
    inputEl.focus()
    expect(document.activeElement).toBe(inputEl)

    // 第一次失败的轮询
    await vi.advanceTimersByTimeAsync(10000)
    await flushPromises()

    expect(wrapper.find('input').exists(), '输入框被卸载了').toBe(true)
    expect(document.activeElement, '焦点被抢走了').toBe(inputEl)
  })

  it('轮询期间不得整页退回 loading（会把输入框整体卸载）', async () => {
    const wrapper = mountPage()
    await settle()
    expect(wrapper.find('input').exists()).toBe(true)

    for (let i = 0; i < 4; i++) {
      await vi.advanceTimersByTimeAsync(10000)
      const loading = wrapper.find('.animate-spin')
      expect(loading.exists(), `第 ${i + 1} 次轮询后不应出现整页 loading`).toBe(false)
      await flushPromises()
    }
  })
})
