/**
 * 错误处理工具函数
 * 用于从 unknown 类型的错误中提取可读的错误消息
 */

/**
 * 从 unknown 错误类型中提取错误消息
 * @param error - 未知类型的错误
 * @returns 错误消息字符串
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'object' && error !== null && 'message' in error) {
    const msg = (error as { message: unknown }).message
    if (typeof msg === 'string') {
      return msg
    }
  }
  if (typeof error === 'string') {
    return error
  }
  return '操作失败'
}
