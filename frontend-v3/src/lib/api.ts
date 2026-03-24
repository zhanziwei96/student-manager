import { ofetch } from 'ofetch'
import type { ApiResponse } from '@/types'

/**
 * Create API client with default configuration
 * Based on: https://github.com/unjs/ofetch
 */
export const api = ofetch.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  credentials: 'include', // Include cookies for JWT authentication
  headers: {
    'Content-Type': 'application/json',
  },
  async onResponseError({ response, request }) {
    // 获取错误消息
    const message = response._data?.message || response.statusText || '请求失败'
    
    // 登录接口的 401 错误不自动跳转，让调用方处理（显示错误提示）
    if (response.status === 401 && !request.toString().includes('/login')) {
      window.location.href = '/login'
    }
    
    // 抛出错误，让调用方可以捕获并显示提示
    throw new Error(message)
  },
})

/**
 * Typed API helper functions
 */
export async function get<T>(url: string, params?: Record<string, unknown>): Promise<ApiResponse<T>> {
  return api(url, { method: 'GET', query: params })
}

export async function post<T>(url: string, body?: unknown): Promise<ApiResponse<T>> {
  return api(url, { method: 'POST', body })
}

export async function put<T>(url: string, body?: unknown): Promise<ApiResponse<T>> {
  return api(url, { method: 'PUT', body })
}

export async function del<T>(url: string): Promise<ApiResponse<T>> {
  return api(url, { method: 'DELETE' })
}

export async function patch<T>(url: string, body?: unknown): Promise<ApiResponse<T>> {
  return api(url, { method: 'PATCH', body })
}
