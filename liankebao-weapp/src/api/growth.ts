import { api } from './client'

/* ========================================================================== */
/*  类型定义                                                                   */
/* ========================================================================== */

export interface MetricsData {
  /** 今日收益（分） */
  today_earnings: number
  /** 本月收益（分） */
  month_earnings: number
  /** 总收益（分） */
  total_earnings: number
  /** 本月推广订单数 */
  order_count: number
  /** 团队人数 */
  team_size: number
  /** 团队总收益（分） */
  team_earnings: number
  /** 我的推广码 */
  promo_code: string
  /** 推广海报URL（后端生成时提供） */
  promo_poster_url?: string
}

export interface TrendItem {
  date: string       // '07-01'
  earnings: number   // 分
}

export interface ProductItem {
  id: string
  name: string
  description: string
  commission: number    // 佣金（分）
  commission_rate: number // 佣金比例 0-100
  sales_count: number
  promo_link: string
  cover_image?: string
}

export interface SubPromoter {
  id: string
  nickname: string
  avatar: string
  level: number
  order_count: number
  earnings: number       // 贡献收益（分）
  active_days: number
}

export interface EarningsDetail {
  id: string
  type: 'commission' | 'team_bonus' | 'withdraw'
  amount: number
  status: 'pending' | 'settled' | 'failed'
  order_id?: string
  product_name?: string
  created_at: string
}

/* ========================================================================== */
/*  API                                                                       */
/* ========================================================================== */

const growthApi = {
  /** 获取增长指标（收益概览） */
  getMetrics: () => {
    return api.get<MetricsData>('/api/v1/growth/metrics')
  },

  /** 获取收益趋势 */
  getTrends: ({ days = 7 }: { days?: number } = {}) => {
    return api.get<TrendItem[]>('/api/v1/growth/trends', { data: { days } })
  },

  /** 获取可推广商品列表 */
  getProducts: () => {
    return api.get<ProductItem[]>('/api/v1/growth/products')
  },

  /** 获取下级推广员列表 */
  getSubPromoters: () => {
    return api.get<SubPromoter[]>('/api/v1/growth/sub-promoters')
  },

  /** 获取收益明细 */
  getEarningsDetails: ({ page = 1, page_size = 20 }: { page?: number; page_size?: number } = {}) => {
    return api.get<EarningsDetail[]>('/api/v1/growth/earnings-details', { data: { page, page_size } })
  },
}

export default growthApi
