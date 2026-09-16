/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock lib/api before importing lostFoundApi
vi.mock('@/lib/api', () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
}))

import { createLostFoundItem, updateLostFoundItem } from '@/api/lostFound'
import { post, put } from '@/lib/api'

describe('lostFoundApi 班级多选', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('createLostFoundItem', () => {
    it('勾选班级时每个班级追加一个 class_ids 重复字段', async () => {
      vi.mocked(post).mockResolvedValue({ item_id: 1 })

      await createLostFoundItem({
        title: '校园卡',
        description: '在食堂捡到',
        class_ids: [3, 7],
      })

      expect(post).toHaveBeenCalledWith('/teacher/lost-found', expect.any(FormData))
      const body = vi.mocked(post).mock.calls[0][1] as FormData
      expect(body.getAll('class_ids')).toEqual(['3', '7'])
      expect(body.get('title')).toBe('校园卡')
    })

    it('空选不传任何 class_ids 字段（后端默认 = 所有班级可见）', async () => {
      vi.mocked(post).mockResolvedValue({ item_id: 2 })

      await createLostFoundItem({
        title: '雨伞',
        description: '图书馆门口',
        class_ids: [],
      })

      const body = vi.mocked(post).mock.calls[0][1] as FormData
      expect(body.getAll('class_ids')).toEqual([])
    })

    it('未提供 class_ids 时同样不传', async () => {
      vi.mocked(post).mockResolvedValue({ item_id: 3 })

      await createLostFoundItem({ title: '钥匙', description: '操场' })

      const body = vi.mocked(post).mock.calls[0][1] as FormData
      expect(body.getAll('class_ids')).toEqual([])
    })
  })

  describe('updateLostFoundItem', () => {
    it('勾选班级时每个班级追加一个 class_ids 重复字段', async () => {
      vi.mocked(put).mockResolvedValue(undefined)

      await updateLostFoundItem(9, { class_ids: [1, 2, 5] })

      expect(put).toHaveBeenCalledWith('/teacher/lost-found/9', expect.any(FormData))
      const body = vi.mocked(put).mock.calls[0][1] as FormData
      expect(body.getAll('class_ids')).toEqual(['1', '2', '5'])
    })

    it('空选不传任何 class_ids 字段（后端 None = 保持原范围）', async () => {
      vi.mocked(put).mockResolvedValue(undefined)

      await updateLostFoundItem(9, { title: '新标题', class_ids: [] })

      const body = vi.mocked(put).mock.calls[0][1] as FormData
      expect(body.getAll('class_ids')).toEqual([])
      expect(body.get('title')).toBe('新标题')
    })
  })
})
