/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { computed } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Leaderboard from '@/views/student/Leaderboard.vue'

// Mock auth store（当前登录学生）
vi.mock('@/stores', () => ({
  useAuthStore: () => ({
    user: { id: 'S001', name: '张三', role: 'student' }
  })
}))

// 可变的 mock 数据（beforeEach 中重置，各用例可覆盖）
const holder = vi.hoisted(() => ({
  subjects: [] as Array<{ id: number; name: string; semester: string }>,
  term: '2026春',
  subjectScores: [] as Array<{
    subject_id: number
    subject_name: string
    teacher_id: number
    teacher_name: string
    score: number
  }>,
  leaderboardCalls: [] as Array<Record<string, unknown>>,
}))

// Mock 科目列表（组件 setup 时读取 holder 当前值）
vi.mock('@/composables/useSubjects', () => ({
  useSubjects: () => ({
    data: computed(() => holder.subjects),
    isPending: computed(() => false),
    error: computed(() => null),
    refetch: vi.fn(),
  }),
}))

// Mock 当前学期信息
vi.mock('@/composables/useTermInfo', () => ({
  useTermInfo: () => ({
    data: computed(() => ({ term: holder.term, start_date: '2026-02-01', current_week: 1, total_weeks: 20 })),
    isPending: computed(() => false),
    error: computed(() => null),
  }),
}))

// Mock 学生科目分数 API（教师筛选器的数据来源）
vi.mock('@/api/students', () => ({
  studentsApi: {
    getSubjects: () => Promise.resolve(holder.subjectScores),
  },
}))

// Mock lib/api 的 get：排行榜请求走它，记录每次调用参数
vi.mock('@/lib/api', () => ({
  get: (url: string, params?: Record<string, unknown>) => {
    if (url === '/students/leaderboard') {
      holder.leaderboardCalls.push({ ...(params ?? {}) })
      return Promise.resolve({ scope: 'class', students: [], total: 0, my_rank: null })
    }
    return Promise.resolve(null)
  },
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  })

  return mount(Leaderboard, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: ['RouterLink']
    }
  })
}

describe('Student Leaderboard', () => {
  beforeEach(() => {
    holder.subjects = [
      { id: 1, name: '数学', semester: '2026春' },
      { id: 2, name: '语文', semester: '2026春' },
      { id: 3, name: '旧科目', semester: '2025秋' },
    ]
    holder.term = '2026春'
    holder.subjectScores = [
      { subject_id: 1, subject_name: '数学', teacher_id: 10, teacher_name: '王老师', score: 90 },
      { subject_id: 2, subject_name: '语文', teacher_id: 20, teacher_name: '李老师', score: 85 },
    ]
    holder.leaderboardCalls = []
  })

  it('默认选中当前学期第一个科目', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const subjectSelect = wrapper.find('[data-testid="subject-filter"]').find('select')
    expect((subjectSelect.element as HTMLSelectElement).value).toBe('1')

    // 排行榜请求带默认科目参数
    expect(holder.leaderboardCalls.at(-1)).toMatchObject({ scope: 'class', subject_id: 1 })
  })

  it('科目筛选器只显示当前学期科目', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const labels = wrapper.find('[data-testid="subject-filter"]').findAll('option').map((o) => o.text())
    expect(labels).toContain('全部科目')
    expect(labels).toContain('数学')
    expect(labels).toContain('语文')
    expect(labels).not.toContain('旧科目')
  })

  it('filters by subject and teacher', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    // 切换科目为语文
    await wrapper.find('[data-testid="subject-filter"]').find('select').setValue('2')
    await flushPromises()
    expect(holder.leaderboardCalls.at(-1)).toMatchObject({ subject_id: 2 })

    // 教师选项随科目变化（只显示语文老师）
    const teacherLabels = wrapper.find('[data-testid="teacher-filter"]').findAll('option').map((o) => o.text())
    expect(teacherLabels).toContain('全部教师')
    expect(teacherLabels).toContain('李老师')
    expect(teacherLabels).not.toContain('王老师')

    // 选择教师后请求带 teacher_id
    await wrapper.find('[data-testid="teacher-filter"]').find('select').setValue('20')
    await flushPromises()
    expect(holder.leaderboardCalls.at(-1)).toMatchObject({ subject_id: 2, teacher_id: 20 })
  })

  it('选择全部科目时回退到 scope 排行榜', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    await wrapper.find('[data-testid="subject-filter"]').find('select').setValue('')
    await flushPromises()

    const last = holder.leaderboardCalls.at(-1)!
    expect(last.subject_id).toBeUndefined()
    expect(last.scope).toBe('class')
  })
})
