import { api } from '@/lib/api'
import type {
  ApiResponse,
  StatsData,
  DashboardData,
} from '@/types'

export const statsApi = {
  getStats: (): Promise<ApiResponse<StatsData>> =>
    api('/stats', { method: 'GET' }),

  getDashboard: (): Promise<ApiResponse<DashboardData>> =>
    api('/dashboard', { method: 'GET' }),
}
