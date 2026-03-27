/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Dashboard from '@/views/admin/Dashboard.vue'

// Mock API
vi.mock('@/api/stats', () => ({
  statsApi: {
    getStats: vi.fn(() => Promise.resolve({
      total_students: 100,
      active_students: 80,
      total_classes: 5,
      average_score: 85
    }))
  }
}))

vi.mock('@/api/checkin', () => ({
  checkinApi: {
    getActiveSessions: vi.fn()
  }
}))

// Mock composables
vi.mock('@/composables', () => ({
  useStats: () => ({
    data: ref({
      total_students: 100,
      active_students: 80,
      total_classes: 5,
      average_score: 85
    }),
    isPending: ref(false),
    error: ref(null)
  })
}))

import { checkinApi } from '@/api/checkin'

// Mock date utils
vi.mock('@/lib/date', () => ({
  formatDistanceToNow: vi.fn((date: string) => '10分钟前')
}))

const MockCard = {
  template: '<div class="mock-card"><slot /></div>'
}

const MockBadge = {
  props: ['variant'],
  template: '<span class="mock-badge"><slot /></span>'
}

describe('Dashboard Active Classes', () => {
  const createTestQueryClient = () => new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 }
    }
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mountComponent = (activeSessionsData = []) => {
    const queryClient = createTestQueryClient()
    
    // Setup mock
    vi.mocked(checkinApi.getActiveSessions).mockResolvedValue(activeSessionsData)

    return mount(Dashboard, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs: {
          Card: MockCard,
          Badge: MockBadge
        }
      }
    })
  }

  it('displays active classes with correct format', async () => {
    const activeSessions = [
      {
        course_name: '高等数学',
        class_name: '计算机1班',
        teacher_name: '张老师',
        start_time: '2024-01-15T08:00:00Z'
      },
      {
        course_name: '大学英语',
        class_name: '软件工程班',
        teacher_name: '李老师',
        start_time: '2024-01-15T09:30:00Z'
      }
    ]

    const wrapper = mountComponent(activeSessions)
    await flushPromises()

    // 验证标题
    expect(wrapper.text()).toContain('正在上课')
    expect(wrapper.text()).toContain('2 个课堂')

    // 验证格式：【课程】班级 | 老师
    expect(wrapper.text()).toContain('【高等数学】')
    expect(wrapper.text()).toContain('计算机1班')
    expect(wrapper.text()).toContain('张老师')
    
    expect(wrapper.text()).toContain('【大学英语】')
    expect(wrapper.text()).toContain('软件工程班')
    expect(wrapper.text()).toContain('李老师')
  })

  it('displays empty state when no active classes', async () => {
    const wrapper = mountComponent([])
    await flushPromises()

    // 验证空状态
    expect(wrapper.text()).toContain('正在上课')
    expect(wrapper.text()).toContain('0 个课堂')
    expect(wrapper.text()).toContain('暂无正在上课的课堂')
  })

  it('handles missing course_name gracefully', async () => {
    const activeSessions = [
      {
        course_name: null,
        class_name: '未知课程班级',
        teacher_name: '王老师',
        start_time: '2024-01-15T10:00:00Z'
      }
    ]

    const wrapper = mountComponent(activeSessions)
    await flushPromises()

    // 验证显示"未知课程"
    expect(wrapper.text()).toContain('【未知课程】')
    expect(wrapper.text()).toContain('未知课程班级')
  })

  it('shows loading state', async () => {
    const queryClient = createTestQueryClient()
    
    // 模拟加载中
    vi.mocked(checkinApi.getActiveSessions).mockImplementation(() => 
      new Promise(() => {}) // 永远不 resolve
    )

    const wrapper = mount(Dashboard, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs: { Card: MockCard, Badge: MockBadge }
      }
    })
    
    await flushPromises()

    // 验证加载状态
    expect(wrapper.text()).toContain('正在上课')
  })

  it('displays start time in relative format', async () => {
    const activeSessions = [
      {
        course_name: '程序设计',
        class_name: '人工智能班',
        teacher_name: '刘老师',
        start_time: new Date().toISOString()
      }
    ]

    const wrapper = mountComponent(activeSessions)
    await flushPromises()

    // 验证显示相对时间
    expect(wrapper.text()).toContain('开始于 10分钟前')
  })
})
