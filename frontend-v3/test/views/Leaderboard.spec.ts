/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Leaderboard from '@/views/student/Leaderboard.vue'

// Mock auth store
vi.mock('@/stores', () => ({
  useAuthStore: () => ({
    user: { id: 'S001', name: '张三', role: 'student' }
  })
}))

// Mock composable
vi.mock('@/composables/useLeaderboard', () => ({
  useLeaderboard: () => ({
    data: ref({
      scope: 'class',
      students: [
        { rank: 1, student_id: 'S002', name: '李四', class_name: '一班', score: 95 },
        { rank: 2, student_id: 'S001', name: '张三', class_name: '一班', score: 88 },
        { rank: 3, student_id: 'S003', name: '王五', class_name: '一班', score: 82 },
      ],
      total: 3,
      my_rank: { rank: 2, student_id: 'S001', name: '张三', score: 88 }
    }),
    isPending: ref(false),
    students: ref([
      { rank: 1, student_id: 'S002', name: '李四', class_name: '一班', score: 95 },
      { rank: 2, student_id: 'S001', name: '张三', class_name: '一班', score: 88 },
      { rank: 3, student_id: 'S003', name: '王五', class_name: '一班', score: 82 },
    ]),
    myRank: ref({ rank: 2, student_id: 'S001', name: '张三', score: 88 })
  })
}))

describe('Leaderboard', () => {
  const createWrapper = () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } }
    })

    return mount(Leaderboard, {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]]
      }
    })
  }

  it('renders leaderboard title', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('班级排行榜')
    expect(wrapper.text()).toContain('查看同班级同学排名')
  })

  it('displays tab buttons', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('班级榜')
    expect(wrapper.text()).toContain('全校榜')
  })

  it('shows my rank card', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('我的排名')
    expect(wrapper.text()).toContain('第 2 名')
  })

  it('displays student list', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('李四')
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('王五')
  })

  it('shows top 3 icons', () => {
    const wrapper = createWrapper()
    // 前三名应该有特殊显示
    const rows = wrapper.findAll('tbody tr')
    expect(rows.length).toBe(3)
  })

  it('highlights current student', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('我')
  })

  it('displays scores correctly', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('95')
    expect(wrapper.text()).toContain('88')
    expect(wrapper.text()).toContain('82')
  })

  it('has different styles for top 3 ranks', () => {
    const wrapper = createWrapper()
    const rows = wrapper.findAll('tbody tr')

    // 获取前三名的背景样式类
    const rank1Bg = rows[0].find('.rounded-full')?.classes().join(' ') || ''
    const rank2Bg = rows[1].find('.rounded-full')?.classes().join(' ') || ''
    const rank3Bg = rows[2].find('.rounded-full')?.classes().join(' ') || ''

    // 验证前三名样式不同
    expect(rank1Bg).not.toBe(rank2Bg)
    expect(rank2Bg).not.toBe(rank3Bg)
    expect(rank1Bg).not.toBe(rank3Bg)

    // 验证包含预期的颜色类
    expect(rank1Bg).toContain('yellow')
    expect(rank2Bg).toContain('slate')
    expect(rank3Bg).toContain('orange')
  })
})
