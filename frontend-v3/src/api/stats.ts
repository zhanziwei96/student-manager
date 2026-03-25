import { get } from '@/lib/api'
import type { StatsData, DashboardData } from '@/types'

/**
 * 统计数据 API - FE-003 修复后
 *
 * 调用方无需再检查 res.success，错误会自动抛出
 * 返回类型直接是数据 T，而不是 ApiResponse<T>
 */
export const statsApi = {
  getStats: (): Promise<StatsData> =>
    get('/stats'),

  getDashboard: (): Promise<DashboardData> =>
    get('/dashboard'),
}
