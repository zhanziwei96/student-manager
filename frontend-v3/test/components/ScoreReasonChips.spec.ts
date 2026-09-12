/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ScoreReasonChips from '@/components/teacher/ScoreReasonChips.vue'
import { SCORE_REASON_PRESETS } from '@/lib/scoreReasons'

describe('ScoreReasonChips 加减分快捷标签', () => {
  it('渲染全部预设，加分显示 +N、减分显示 -N', () => {
    const wrapper = mount(ScoreReasonChips)

    expect(wrapper.findAll('button')).toHaveLength(SCORE_REASON_PRESETS.length)
    expect(wrapper.text()).toContain('课堂积极发言 +2')
    expect(wrapper.text()).toContain('旷课 -5')
  })

  it('点击标签抛出 pick 事件，携带原因与分值', async () => {
    const wrapper = mount(ScoreReasonChips)

    await wrapper.find('[data-testid="score-preset-作业未交"]').trigger('click')

    expect(wrapper.emitted('pick')?.[0]).toEqual([{ label: '作业未交', delta: -2 }])
  })

  it('预设内容符合约定：加分全为 +2，减分仅三项', () => {
    const plus = SCORE_REASON_PRESETS.filter((p) => p.delta > 0)
    const minus = SCORE_REASON_PRESETS.filter((p) => p.delta < 0)

    expect(plus.every((p) => p.delta === 2)).toBe(true)
    expect(minus.map((p) => [p.label, p.delta])).toEqual([
      ['课堂违纪', -2],
      ['作业未交', -2],
      ['旷课', -5],
    ])
  })
})
