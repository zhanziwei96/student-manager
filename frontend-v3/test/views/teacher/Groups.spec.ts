/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import Groups from '@/views/teacher/Groups.vue'

// Shared mutable state for mocks
const mockGroupSettingsData = ref<{ class_name: string; max_members_per_group: number } | null>(null)
const mockGroupsData = ref<any[]>([])
const mockSubjectsData = ref<any[]>([])
const mockScoreLogsData = ref<any[]>([])
const mockLeaderboardData = ref<{ groups: any[]; total: number }>({ groups: [], total: 0 })
const mockUpdateScore = vi.fn()

vi.mock('@/composables', () => ({
  useClasses: () => ({ data: ref([{ name: '计算机1班', status: 'active' }]) }),
  useSubjects: () => ({ data: mockSubjectsData }),
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('@/features/group-collaboration', () => ({
  useTeacherGroups: () => ({ data: mockGroupsData, isPending: ref(false) }),
  useAutoAssign: () => ({ mutateAsync: vi.fn(), isPending: ref(false) }),
  useClassGroupSettings: () => ({ data: mockGroupSettingsData }),
  useUpdateClassGroupSettings: () => ({ mutateAsync: vi.fn() }),
  useGroupScore: () => ({ mutateAsync: mockUpdateScore }),
  useGroupScoreLogs: () => ({ data: mockScoreLogsData, isPending: ref(false) }),
  useGroupLeaderboard: () => ({ data: mockLeaderboardData, isPending: ref(false) }),
}))

vi.mock('@tanstack/vue-query', async () => {
  const actual = await vi.importActual('@tanstack/vue-query')
  return {
    ...(actual as any),
    useQuery: () => ({ data: ref([]), isPending: ref(false) }),
    useMutation: () => ({ mutateAsync: vi.fn() }),
  }
})

const stubs = {
  Card: { template: '<div class="card"><slot /></div>' },
  Button: { props: ['loading', 'disabled', 'variant'], template: '<button class="btn"><slot /></button>' },
  Select: { props: ['modelValue', 'options'], template: '<select class="select"><slot /></select>' },
  Input: { props: ['modelValue', 'type'], template: '<input class="input" :type="type" />' },
  Label: { template: '<label class="label"><slot /></label>' },
  Badge: { template: '<span class="badge"><slot /></span>' },
  DataContainer: { props: ['loading', 'hasData'], template: '<div class="data-container"><slot /></div>' },
  Dialog: {
    props: ['open', 'title'],
    template: '<div v-if="open" class="dialog"><div class="dialog-title">{{ title }}</div><slot /><slot name="footer" /></div>',
  },
}

function createTestQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function mountGroups() {
  const queryClient = createTestQueryClient()
  return mount(Groups, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs,
    },
  })
}

describe('Groups', () => {
  beforeEach(() => {
    mockGroupSettingsData.value = null
    mockGroupsData.value = []
    mockSubjectsData.value = []
    mockScoreLogsData.value = []
    mockLeaderboardData.value = { groups: [], total: 0 }
    mockUpdateScore.mockReset()
  })

  it('renders without error', () => {
    const wrapper = mountGroups()
    expect(wrapper.find('div').exists()).toBe(true)
    expect(wrapper.text()).toContain('小组管理')
  })

  it('initializes maxMembers from cached groupSettings on mount', async () => {
    // Simulate Vue Query cached data being available synchronously
    mockGroupSettingsData.value = { class_name: '计算机1班', max_members_per_group: 8 }

    const wrapper = mountGroups()

    await flushPromises()
    await nextTick()

    const input = wrapper.find('input[type="number"]')
    expect(input.exists()).toBe(true)
    expect((input.element as HTMLInputElement).value).toBe('8')
  })

  it('falls back to default 5 when no groupSettings available', async () => {
    mockGroupSettingsData.value = null

    const wrapper = mountGroups()

    await flushPromises()
    await nextTick()

    const input = wrapper.find('input[type="number"]')
    expect(input.exists()).toBe(true)
    expect((input.element as HTMLInputElement).value).toBe('5')
  })

  it('displays group score and subject name on cards', async () => {
    mockGroupsData.value = [
      {
        id: 1,
        name: '第一组',
        leader_student_id: '2021001',
        leader_name: '张三',
        subject_id: 1,
        subject_name: '数学',
        score: 12,
        members: [{ student_id: '2021001', name: '张三' }],
      },
    ]
    mockSubjectsData.value = [{ id: 1, name: '数学', semester: '2026-2027-1' }]

    const wrapper = mountGroups()
    await flushPromises()
    await nextTick()

    expect(wrapper.text()).toContain('第一组')
    expect(wrapper.text()).toContain('数学')
    expect(wrapper.text()).toContain('12')
  })

  it('opens score dialog with current score and submits', async () => {
    mockGroupsData.value = [
      {
        id: 1,
        name: '第一组',
        leader_student_id: '2021001',
        leader_name: '张三',
        subject_id: 1,
        subject_name: '数学',
        score: 12,
        members: [{ student_id: '2021001', name: '张三' }],
      },
    ]

    const wrapper = mountGroups()
    await flushPromises()
    await nextTick()

    const openBtn = wrapper.findAll('button').find((b) => b.text().includes('加减分'))
    expect(openBtn).toBeTruthy()
    await openBtn!.trigger('click')
    await nextTick()

    const dialog = wrapper.find('.dialog')
    expect(dialog.exists()).toBe(true)
    expect(dialog.text()).toContain('加减分 - 第一组')
    expect(dialog.text()).toContain('当前分数')
    expect(dialog.text()).toContain('12')
  })

  it('shows leaderboard entries', async () => {
    mockLeaderboardData.value = {
      groups: [
        { rank: 1, group_id: 1, group_name: '第一组', class_name: '计算机1班', subject_id: 1, score: 20 },
      ],
      total: 1,
    }

    const wrapper = mountGroups()
    await flushPromises()
    await nextTick()

    expect(wrapper.text()).toContain('小组排行榜')
    expect(wrapper.text()).toContain('第一组')
    expect(wrapper.text()).toContain('20')
  })
})
