/**
 * @vitest-environment jsdom
 *
 * 管理员签到管理页：按活跃课堂取签到统计
 * （曾因未传 session_id 导致统计恒为 0）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import Checkins from '@/views/admin/Checkins.vue'

const holder = vi.hoisted(() => ({
  sessions: [] as unknown[],
  stats: {} as Record<string, unknown>,
  // 组件传入的是 computed ref，记录 ref 本身才能观察到切换（真实 composable 也是响应式的）
  sessionIdRef: undefined as { value?: number } | undefined,
}))

vi.mock('@/composables/useCourseSessions', () => ({
  useActiveClassSessions: () => ({
    data: ref(holder.sessions),
    isPending: ref(false),
  }),
}))

vi.mock('@/composables/useCheckins', () => ({
  useSessionCheckinStats: (sessionId: { value?: number }) => {
    holder.sessionIdRef = sessionId
    return { data: ref(holder.stats) }
  },
}))

const mountComponent = () => mount(Checkins, {
  global: {
    stubs: {
      Card: { template: '<div class="mock-card"><slot /></div>' },
      Select: {
        name: 'Select',
        props: ['modelValue', 'options'],
        emits: ['update:modelValue'],
        template: `
          <select class="mock-select" :value="modelValue" @change="$emit('update:modelValue', Number($event.target.value))">
            <option v-for="opt in options || []" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        `,
      },
    },
  },
})

describe('Admin Checkins - 按活跃课堂统计', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    holder.sessions = []
    holder.stats = {}
    holder.sessionIdRef = undefined
  })

  it('没有进行中的课堂时显示空状态且不显示统计卡', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('当前没有进行中的课堂')
    expect(wrapper.text()).not.toContain('签到率')
    expect(holder.sessionIdRef?.value).toBeUndefined()  // 无课堂时不该按 undefined 请求
  })

  it('有活跃课堂时按其 id 拉取统计并渲染数值', async () => {
    holder.sessions = [
      { id: 7, course_name: '高等数学', class_name: '2026届软件工程1班', teacher_name: '张老师', start_time: '2026-09-12T08:00:00' },
    ]
    holder.stats = { active: true, total: 40, checked_in: 30, not_checked_in: 10, rate: 75 }

    const wrapper = mountComponent()
    await flushPromises()

    expect(holder.sessionIdRef?.value).toBe(7)
    expect(wrapper.text()).toContain('40')
    expect(wrapper.text()).toContain('30')
    expect(wrapper.text()).toContain('10')
    expect(wrapper.text()).toContain('75%')
  })

  it('多个课堂时提供切换并切换到所选课堂', async () => {
    holder.sessions = [
      { id: 7, course_name: '高等数学', class_name: '一班', teacher_name: '张老师', start_time: '2026-09-12T08:00:00' },
      { id: 8, course_name: '大学英语', class_name: '二班', teacher_name: '李老师', start_time: '2026-09-12T09:00:00' },
    ]
    holder.stats = { active: true, total: 40, checked_in: 4, not_checked_in: 36, rate: 10 }

    const wrapper = mountComponent()
    await flushPromises()
    expect(holder.sessionIdRef?.value).toBe(7)  // 默认第一个

    const select = wrapper.find('select.mock-select')
    expect(select.findAll('option')).toHaveLength(2)
    await select.setValue('8')
    await flushPromises()

    expect(holder.sessionIdRef?.value).toBe(8)
  })
})
