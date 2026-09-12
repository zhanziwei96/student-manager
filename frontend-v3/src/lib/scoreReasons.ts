/**
 * 加减分快捷选项（个人成绩 / 小组共用）
 *
 * 点选后同时填入原因与建议分值，教师仍可手改或直接自定义原因。
 */
export interface ScoreReasonPreset {
  label: string
  delta: number
}

export const SCORE_REASON_PRESETS: readonly ScoreReasonPreset[] = [
  // 加分
  { label: '课堂积极发言', delta: 2 },
  { label: '课堂表现优秀', delta: 2 },
  { label: '作业完成优秀', delta: 2 },
  { label: '小组协作积极', delta: 2 },
  { label: '帮助同学/答疑', delta: 2 },
  { label: '进步明显', delta: 2 },
  { label: '全勤', delta: 2 },
  { label: '竞赛/活动获奖', delta: 2 },
  // 减分
  { label: '课堂违纪', delta: -2 },
  { label: '作业未交', delta: -2 },
  { label: '旷课', delta: -5 },
]
