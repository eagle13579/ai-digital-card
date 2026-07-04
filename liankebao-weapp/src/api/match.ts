import { api } from './client'

export interface RecommendItem {
  id: string
  card_id: string
  name: string
  company: string
  title: string
  avatar: string
  match_score: number
  match_reason: string
  tags: string[]
}

export interface SupplyDemandItem {
  id: string
  title: string
  company: string
  industry: string
  /** 匹配度 0–100 */
  match_score: number
  publish_time: string
  description?: string
  contact?: string
  user_id?: string
  purpose?: 'supply' | 'demand'
  /** AI推荐理由（仅 AI 推荐 Tab 使用） */
  match_reason?: string
}

export interface SupplyDemandListParams {
  page?: number
  page_size?: number
  purpose?: string
}

export interface SupplyDemandListResponse {
  list: SupplyDemandItem[]
  total: number
  page: number
  page_size: number
}

const matchApi = {
  /** AI混合推荐 */
  getHybridRecommend: (cardId: string) => {
    return api.get(`/api/v1/ai/recommend/hybrid/${cardId}`)
  },
  /** 供需列表 */
  getMatches: (params?: SupplyDemandListParams) => {
    return api.get<SupplyDemandListResponse>('/api/v1/matches', { data: params as any })
  },
}

export default matchApi
