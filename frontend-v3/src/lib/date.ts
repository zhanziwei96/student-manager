/**
 * 日期工具函数
 */

/**
 * 格式化时间为相对时间（如：2分钟前、1小时前）
 */
export function formatDistanceToNow(date: string | Date): string {
  const now = new Date()
  const target = typeof date === 'string' ? new Date(date) : date
  const diffMs = now.getTime() - target.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffSec < 60) {
    return '刚刚'
  } else if (diffMin < 60) {
    return `${diffMin}分钟前`
  } else if (diffHour < 24) {
    return `${diffHour}小时前`
  } else if (diffDay < 30) {
    return `${diffDay}天前`
  } else {
    return target.toLocaleDateString('zh-CN')
  }
}

/**
 * 格式化日期时间为本地字符串
 */
export function formatDateTime(date: string | Date): string {
  const target = typeof date === 'string' ? new Date(date) : date
  return target.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * 格式化日期为本地字符串
 */
export function formatDate(date: string | Date): string {
  const target = typeof date === 'string' ? new Date(date) : date
  return target.toLocaleDateString('zh-CN')
}

/**
 * 格式化时间为本地字符串
 */
export function formatTime(date: string | Date): string {
  const target = typeof date === 'string' ? new Date(date) : date
  return target.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * 获取当前周次（基于学期开始日期）
 * 第二学期改造：基准日期由后端 GET /api/term/current 下发，
 * 不再硬编码；开学前返回 0（UI 显示"未开学"）。
 *
 * @param termStartDate 学期开始日期（第 1 周周一，ISO 字符串）
 * @param totalWeeks 学期总周数
 * @returns 当前周次：0=未开学，1..totalWeeks=学期中
 */
export function getCurrentWeek(
  termStartDate?: string | null,
  totalWeeks = 20,
): number {
  // 无学期基准时返回 1（向后兼容，避免全站误显示）
  if (!termStartDate) return 1

  const start = new Date(termStartDate)
  const now = new Date()

  // 开学前返回 0
  if (now < start) return 0

  const msPerWeek = 7 * 24 * 60 * 60 * 1000
  const diff = Math.floor((now.getTime() - start.getTime()) / msPerWeek)
  return Math.min(diff + 1, totalWeeks)
}
