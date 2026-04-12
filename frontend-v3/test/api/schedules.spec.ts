/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock lib/api before importing schedulesApi
vi.mock('@/lib/api', () => ({
  get: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
  api: vi.fn(),
  post: vi.fn(),
}))

import { schedulesApi } from '@/api/schedules'
import { post, api } from '@/lib/api'

describe('schedulesApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('import', () => {
    it('应使用 post 发送 FormData 并返回导入结果', async () => {
      const mockResult = { imported: 5, errors: [] }
      vi.mocked(post).mockResolvedValue(mockResult)

      const file = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const result = await schedulesApi.import(file)

      expect(post).toHaveBeenCalledTimes(1)
      expect(post).toHaveBeenCalledWith('/schedules/import', expect.any(FormData))

      const passedBody = vi.mocked(post).mock.calls[0][1] as FormData
      expect(passedBody.get('file')).toBe(file)
      expect(result).toEqual(mockResult)
    })

    it('当后端返回错误时应抛出 ApiError', async () => {
      vi.mocked(post).mockRejectedValue(new Error('文件格式错误'))

      const file = new File(['test'], 'test.csv', { type: 'text/csv' })
      await expect(schedulesApi.import(file)).rejects.toThrow('文件格式错误')
    })
  })

  describe('downloadTemplate', () => {
    it('应通过 api 获取 Blob', async () => {
      const mockBlob = new Blob(['test'], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      vi.mocked(api).mockResolvedValue(mockBlob)

      const result = await schedulesApi.downloadTemplate()

      expect(api).toHaveBeenCalledTimes(1)
      expect(api).toHaveBeenCalledWith('/schedules/template', { method: 'GET', responseType: 'blob' })
      expect(result).toBe(mockBlob)
    })
  })
})
