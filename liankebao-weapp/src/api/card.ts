import Taro from '@tarojs/taro'
import { API_BASE_URL } from '../config/env'
import { api } from './client'

export interface CardData {
  id: string
  user_id: string
  name: string
  company: string
  title: string
  phone: string
  email: string
  avatar: string
  wechat_qrcode: string
  bg_image: string
  theme: string
  style_config: Record<string, any>
  fields: Record<string, any>
  is_public: boolean
  created_at: string
  updated_at: string
}

export interface CardListParams {
  page?: number
  page_size?: number
}

export interface CardListResponse {
  code: number
  data: {
    list: CardData[]
    total: number
  }
  message?: string
}

/** AI名片扫描返回结果 */
export interface ScanResult {
  nickName?: string
  avatarUrl?: string
  company?: string
  position?: string
  phone?: string
  email?: string
  wechat?: string
  website?: string
}

/** 名片生成提交参数 */
export interface CardGenerateParams {
  nickName: string
  avatarUrl?: string
  company?: string
  position?: string
  phone?: string
  email?: string
  wechat?: string
  website?: string
}

const cardApi = {
  getList: (params?: CardListParams) => {
    return api.get('/api/v1/cards/list', { data: params })
  },
  getDetail: (id: string) => {
    return api.get(`/api/v1/cards/${id}`)
  },
  create: (data: Partial<CardData>) => {
    return api.post('/api/v1/cards', data)
  },
  update: (id: string, data: Partial<CardData>) => {
    return api.put(`/api/v1/cards/${id}`, data)
  },
  /** AI名片扫描：上传图片返回识别结果 */
  scan: (filePath: string) => {
    return Taro.uploadFile({
      url: `${API_BASE_URL}/api/card/scan`,
      filePath,
      name: 'file',
      header: {
        Authorization: `Bearer ${Taro.getStorageSync('token')}`,
      },
    }).then((res) => {
      const body = JSON.parse(res.data)
      if (body.code === 200 || body.code === 0) {
        return body as { code: number; data: ScanResult; message?: string }
      }
      throw new Error(body.message || '识别失败')
    })
  },
  /** 生成名片 */
  generate: (data: CardGenerateParams) => {
    return api.post('/api/card/generate', data as unknown as Record<string, any>)
  },
}

export default cardApi
