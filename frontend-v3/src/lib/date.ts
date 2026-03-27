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
