/**
 * 社交关系 API — 询赋吸收模块
 *
 * 对接后端: /api/business-card/connections/*
 * 关系模式: 双向双行记录（A→B 和 B→A 各一行）
 * 响应格式: { code: number, message: string, data: any }
 */

import { api } from './client'

export interface ConnectionUser {
  id: number
  name: string
  company: string
  title: string
  avatar: string
  connection_id: number
  status: string
  strength: number
  label: string
  created_at: string
}

export interface PendingRequest {
  connection_id: number
  user_id: number
  name: string
  company: string
  title: string
  avatar: string
  source: string
  status: string
  created_at: string
}

export interface PathResult {
  distance: number
  path: Array<{
    id: number
    name: string
    company?: string
    avatar?: string
  }>
  message?: string
}

const connectionApi = {
  /** 发起建联请求（自动创建双向双行记录） */
  request: (targetUserId: number, message = '', source = 'platform') => {
    return api.post<any>('/api/business-card/connections/request', {
      target_user_id: targetUserId,
      message,
      source,
    })
  },

  /** 审核建联请求（同步更新双向记录） */
  review: (connectionId: number, approved: boolean) => {
    return api.put<any>(`/api/business-card/connections/${connectionId}/review`, { approved })
  },

  /** 我的好友/关系列表 */
  list: (status?: string) => {
    const params = status ? { status } : {}
    return api.get<ConnectionUser[]>('/api/business-card/connections', { data: params })
  },

  /** 待审核的建联请求列表 */
  listPending: () => {
    return api.get<PendingRequest[]>('/api/business-card/connections/pending')
  },

  /** BFS社交图谱路径查找（最大3度人脉） */
  findPath: (targetUserId: number) => {
    return api.get<PathResult>(`/api/business-card/connections/path/${targetUserId}`)
  },
}

export default connectionApi
