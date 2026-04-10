/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { get, put, del, api, ApiError } from '@/lib/api'

describe('API utils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('put', () => {
    it('should pass query params correctly', async () => {
      const mockResponse = { success: true, data: null }
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
        headers: new Headers({ 'content-type': 'application/json' }),
      })
      
      // @ts-expect-error - mock global fetch
      global.fetch = mockFetch
      
      try {
        // 调用方式：put(url, body, params) - params 直接是键值对，不是嵌套对象
        await put('/test', null, { teacher_id: 1, teacher_name: '张老师' })
      } catch {
        // 可能会因为响应处理失败，但我们只关心请求参数
      }
      
      // 验证 fetch 被调用时 URL 包含查询参数
      const callArg = mockFetch.mock.calls[0][0]
      expect(callArg).toContain('teacher_id=1')
      expect(callArg).toContain('teacher_name=%E5%BC%A0%E8%80%81%E5%B8%88')
      // 确保没有嵌套的 params
      expect(callArg).not.toContain('params=')
    })
  })

  describe('del', () => {
    it('should pass query params correctly', async () => {
      const mockResponse = { success: true, data: null }
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      // @ts-expect-error - mock global fetch
      global.fetch = mockFetch

      try {
        await del('/test', { id: 123 })
      } catch {
        // 可能会因为响应处理失败，但我们只关心请求参数
      }

      // 验证 fetch 被调用时 URL 包含查询参数
      const callArg = mockFetch.mock.calls[0][0]
      expect(callArg).toContain('id=123')
    })
  })

  describe('ApiError', () => {
    it('should carry statusCode and data from backend response', async () => {
      const mockResponse = {
        success: false,
        message: '该课表在当前周次已存在调课记录',
        data: { id: 4, type: 'cancel' },
      }
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 409,
        json: () => Promise.resolve(mockResponse),
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      // @ts-expect-error - mock global fetch
      global.fetch = mockFetch

      try {
        await api('/schedule-adjustments', { method: 'POST', body: {} })
      } catch (err) {
        expect(err).toBeInstanceOf(ApiError)
        expect((err as ApiError).message).toBe('该课表在当前周次已存在调课记录')
        expect((err as ApiError).statusCode).toBe(409)
        expect((err as ApiError).data).toEqual(mockResponse)
        return
      }
      throw new Error('Expected api call to throw ApiError')
    })

    it('should use statusText when backend message is absent', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: () => Promise.resolve({ error: 'unknown' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      })

      // @ts-expect-error - mock global fetch
      global.fetch = mockFetch

      try {
        await api('/test', { method: 'GET' })
      } catch (err) {
        expect(err).toBeInstanceOf(ApiError)
        expect((err as ApiError).message).toBe('Internal Server Error')
        expect((err as ApiError).statusCode).toBe(500)
        expect((err as ApiError).data).toBeUndefined()
        return
      }
      throw new Error('Expected api call to throw ApiError')
    })
  })
})
