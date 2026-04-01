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
 * 获取当前周次（基于基准日期）
 * 基准设定：2026-03-30 是第4周的周一
 * 根据当前日期与基准日期的差值计算周次
 */
export function getCurrentWeek(): number {
  const now = new Date()
  
  // 基准设定: 2026-03-30 是第4周的周一
  const referenceDate = new Date('2026-03-30') // 第4周周一
  const referenceWeek = 4
  
  // 获取当前日期所在周的周一
  const currentDay = now.getDay() // 0=周日, 1=周一, ...
  const daysSinceMonday = currentDay === 0 ? 6 : currentDay - 1
  const currentMonday = new Date(now)
  currentMonday.setDate(now.getDate() - daysSinceMonday)
  currentMonday.setHours(0, 0, 0, 0)
  
  // 获取基准日期的周一（已经是周一）
  const baseMonday = new Date(referenceDate)
  baseMonday.setHours(0, 0, 0, 0)
  
  // 计算两个周一之间的周数差
  const msPerWeek = 7 * 24 * 60 * 60 * 1000
  const weekDiff = Math.floor((baseMonday.getTime() - currentMonday.getTime()) / msPerWeek)
  
  // 计算当前周次
  const currentWeek = referenceWeek - weekDiff
  
  // 限制在 1-20 周范围内
  return Math.max(1, Math.min(20, currentWeek))
}
