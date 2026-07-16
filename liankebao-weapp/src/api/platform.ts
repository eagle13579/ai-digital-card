/**
 * 资源平台 API — 询赋吸收模块
 *
 * 对接后端: /api/business-card/platforms/*
 * 响应格式: { code: number, message: string, data: any }
 */

import { api } from './client'

export interface Platform {
  id: number
  name: string
  platform_no?: string
  creator_id: number
  annual_fee: number
  description: string
  member_count: number
  resource_count: number
  created_at: string
  updated_at: string
}

export interface PlatformMember {
  id: number
  user_id: number
  name: string
  company: string
  title: string
  avatar: string
  role: 'secretary_general' | 'secretariat' | 'member'
  joined_at: string
}

export interface PlatformCreateParams {
  name: string
  description?: string
  annual_fee?: number
  platform_no?: string
}

export interface PlatformReport {
  platform_id: number
  platform_name: string
  total_members: number
  role_distribution: {
    secretary_general: number
    secretariat: number
    member: number
  }
  coverage: {
    company_count: number
    industry_count: number
  }
}

const platformApi = {
  /** 平台推荐列表（按成员数排序） */
  list: (keyword?: string, skip = 0, limit = 20) => {
    const params: Record<string, any> = { skip, limit }
    if (keyword !== undefined) params.keyword = keyword
    return api.get<Platform[]>('/api/business-card/platforms', { data: params })
  },

  /** 平台详情 */
  getById: (id: number) => {
    return api.get<Platform>(`/api/business-card/platforms/${id}`)
  },

  /** 创建平台（创建者自动成为秘书长） */
  create: (data: PlatformCreateParams) => {
    return api.post<Platform>('/api/business-card/platforms', data)
  },

  /** 更新平台信息 */
  update: (id: number, data: Partial<PlatformCreateParams>) => {
    return api.put<Platform>(`/api/business-card/platforms/${id}`, data)
  },

  /** 成员列表（按角色排序） */
  getMembers: (platformId: number) => {
    return api.get<PlatformMember[]>(`/api/business-card/platforms/${platformId}/members`)
  },

  /** 加入平台（角色=member） */
  join: (platformId: number) => {
    return api.post<any>(`/api/business-card/platforms/${platformId}/join`)
  },

  /** 商业报告（仅秘书长可见） */
  getReport: (platformId: number) => {
    return api.get<PlatformReport>(`/api/business-card/platforms/${platformId}/report`)
  },
}

export default platformApi
