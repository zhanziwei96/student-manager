import { ofetch } from 'ofetch'
import type { ApiResponse } from '@/types'

/**
 * FE-003 统一 API 响应处理
 *
 * 在拦截器中自动处理 res.success 检查：
 * - 成功: 自动提取 res.data 返回
 * - 失败: 自动抛出 Error(res.message)
 *
 * 调用方无需再手动检查 res.success，代码简化：
 *
 * 修复前:
 * ```ts
 * const res = await api.get('/students')
 * if (res.success && res.data) {
 *   return res.data
 * }
 * throw new Error(res.message)
 * ```
 *
 * 修复后:
 * ```ts
 * const data = await api.get('/students') // 直接获取数据
 * // 错误自动抛出，无需手动检查
 * ```
 */

/**
 * 检查响应是否是 ApiResponse 格式
 */
function isApiResponse(data: unknown): data is ApiResponse<unknown> {
  return (
    typeof data === 'object' &&
    data !== null &&
    'success' in data &&
    typeof (data as ApiResponse<unknown>).success === 'boolean'
  )
}

/**
 * 创建基础 API 客户端
 */
export const api = ofetch.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
  },

  async onResponseError({ response, request }) {
    // 优先使用后端返回的错误消息
    const data = response._data
    const message =
      (isApiResponse(data) ? data.message : undefined) ||
      response.statusText ||
      '请求失败'

    // 登录接口的 401 错误不自动跳转，让调用方处理
    if (response.status === 401 && !request.toString().includes('/login')) {
      window.location.href = '/login'
    }

    // 抛出错误，让调用方可以捕获
    throw new Error(message)
  },
})

/**
 * 类型安全的 API 请求函数
 *
 * 自动处理 ApiResponse<T>：
 * - 检查 res.success
 * - 成功时返回 res.data
 * - 失败时抛出 Error(res.message)
 */
async function request<T>(
  url: string,
  options?: Omit<NonNullable<Parameters<typeof api>[1]>, 'body' | 'responseType'> & { body?: unknown }
): Promise<T> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const response = await api<ApiResponse<T>>(url, options as any)

  // 检查是否是 ApiResponse 格式
  if (!isApiResponse(response)) {
    // 不是标准格式，直接返回
    return response as T
  }

  // 检查 success 字段
  if (!response.success) {
    throw new Error(response.message || '请求失败')
  }

  // 返回 data
  return response.data as T
}

/**
 * 带原始响应的 API 请求
 * 需要手动检查 res.success 时使用（特殊场景）
 */
async function requestRaw<T>(
  url: string,
  options?: Omit<NonNullable<Parameters<typeof api>[1]>, 'body' | 'responseType'> & { body?: unknown }
): Promise<ApiResponse<T>> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return api<ApiResponse<T>>(url, options as any)
}

// HTTP 方法封装 - 自动处理响应
export async function get<T>(
  url: string,
  params?: Record<string, unknown>
): Promise<T> {
  return request<T>(url, { method: 'GET', query: params })
}

export async function post<T>(url: string, body?: unknown): Promise<T> {
  return request<T>(url, { method: 'POST', body })
}

export async function put<T>(url: string, body?: unknown): Promise<T> {
  return request<T>(url, { method: 'PUT', body })
}

export async function del<T>(url: string): Promise<T> {
  return request<T>(url, { method: 'DELETE' })
}

export async function patch<T>(url: string, body?: unknown): Promise<T> {
  return request<T>(url, { method: 'PATCH', body })
}

// 导出原始请求方法（特殊场景使用）
export { requestRaw }
