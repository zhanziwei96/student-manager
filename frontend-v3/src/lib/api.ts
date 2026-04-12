import { ofetch } from 'ofetch'
import type { ApiResponse } from '@/types'

/**
 * FE-003 统一 API 响应处理
 *
 * 在拦截器中自动处理响应状态检查：
 * - 成功: 自动提取 data 返回
 * - 失败: 自动抛出带状态码的 ApiError
 *
 * 调用方无需再手动检查 response.success，代码简化：
 *
 * 修复前:
 * ```ts
 * const res = await fetch('/students')
 * const data = await res.json()
 * if (data.success && data.data) {
 *   return data.data
 * }
 * throw new Error(data.message)
 * ```
 *
 * 修复后:
 * ```ts
 * const data = await get<Student[]>('/students') // 直接获取数据
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
 * API 错误类 - 携带后端返回的状态码和完整数据
 */
export class ApiError extends Error {
  statusCode: number
  data?: unknown

  constructor(message: string, statusCode: number, data?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.statusCode = statusCode
    this.data = data
  }
}

/**
 * 创建基础 API 客户端
 *
 * 注意：不全局硬编码 Content-Type，由 ofetch 根据 body 类型自动设置：
 * - 普通对象 → application/json
 * - FormData → 由浏览器自动设置 multipart boundary
 * - Blob → 由浏览器自动设置适当类型
 */
export const api = ofetch.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  credentials: 'include',

  async onResponseError({ response, request }) {
    // 优先使用后端返回的错误消息
    let data = response._data
    // 在测试/某些环境中 _data 可能未填充，尝试手动解析 response body
    if (data === undefined && response.json) {
      try {
        data = await response.json()
      } catch {
        // ignored
      }
    }
    const message =
      (isApiResponse(data) ? data.message : undefined) ||
      response.statusText ||
      '请求失败'

    // 登录接口的 401 错误不自动跳转，让调用方处理
    if (response.status === 401 && !request.toString().includes('/login')) {
      window.location.href = '/login'
    }

    // 抛出错误，让调用方可以捕获完整数据
    throw new ApiError(message, response.status, isApiResponse(data) ? data : undefined)
  },
})

/**
 * 类型安全的 API 请求函数
 *
 * 自动处理 ApiResponse<T>：
 * - 检查 success 字段
 * - 成功时返回 data
 * - 失败时抛出 Error(message)
 */
interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  query?: Record<string, unknown>
  body?: Record<string, unknown> | unknown[] | FormData | Blob | null
}

async function request<T>(url: string, options?: RequestOptions): Promise<T> {
  const response = await api<ApiResponse<T>>(url, (options ?? {}) as any)

  // 检查是否是 ApiResponse 格式
  if (!isApiResponse(response)) {
    // 不是标准格式，直接返回（类型收窄）
    return response as unknown as T
  }

  // 检查 success 字段
  if (!response.success) {
    throw new Error(response.message || '请求失败')
  }

  // 返回 data
  return response.data as unknown as T
}

/**
 * 带原始响应的 API 请求
 * 需要手动检查 success 时使用（特殊场景）
 */
async function requestRaw<T>(url: string, options?: RequestOptions): Promise<ApiResponse<T>> {
  return api<ApiResponse<T>>(url, options as any)
}

// HTTP 方法封装 - 自动处理响应
export async function get<T>(
  url: string,
  params?: Record<string, unknown>,
  options?: Omit<RequestOptions, 'method' | 'query'>
): Promise<T> {
  return request<T>(url, { method: 'GET', query: params, ...options })
}

export async function post<T, B = unknown>(url: string, body?: B): Promise<T> {
  return request<T>(url, { method: 'POST', body: body as RequestOptions['body'] })
}

export async function put<T, B = unknown>(url: string, body?: B, params?: Record<string, unknown>): Promise<T> {
  return request<T>(url, { method: 'PUT', body: body as RequestOptions['body'], query: params })
}

export async function del<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  return request<T>(url, { method: 'DELETE', query: params })
}

export async function patch<T, B = unknown>(url: string, body?: B): Promise<T> {
  return request<T>(url, { method: 'PATCH', body: body as RequestOptions['body'] })
}

// 导出原始请求方法（特殊场景使用）
export { requestRaw }
