/**
 * digitalBrochure.ts — 全面对接后端全部 API
 *
 * 按功能域划分:
 *   authApi      — 认证
 *   cardApi      — 数字名片
 *   matchApi     — AI智能匹配
 *   growthApi    — 人脉成长
 *   pricingApi   — 定价与用量
 *   paymentApi   — 支付
 *   notificationApi — 通知
 *   appStoreApi  — 插件/应用市场
 */

import { api } from './client'

/* ========================================================================== */
/*  认证 API                                                                   */
/* ========================================================================== */

export const authApi = {
  /** 微信小程序静默登录（获取 openId/session） */
  wxMiniLogin(code: string) {
    return api.post('/api/auth/wx-mini-login', { code })
  },

  /** 发送短信验证码 */
  smsCode(phone: string) {
    return api.post('/api/auth/sms-code', { phone })
  },

  /** 短信验证码登录 / 注册 */
  smsLogin(phone: string, code: string) {
    return api.post('/api/auth/sms-login', { phone, code })
  },

  /** 获取当前用户信息 */
  getProfile() {
    return api.get('/api/auth/profile')
  },
}

/* ========================================================================== */
/*  名片 API                                                                   */
/* ========================================================================== */

export interface CardData {
  id?: string
  name: string
  company?: string
  title?: string
  phone?: string
  email?: string
  wechat?: string
  avatar?: string
  /** 名片模板 ID */
  template_id?: string
  /** 自定义字段 */
  fields?: Record<string, any>
  [key: string]: any
}

export const cardApi = {
  /** 获取名片列表（分页） */
  getList(params?: { page?: number; page_size?: number; keyword?: string }) {
    return api.get('/api/card/list', { data: params })
  },

  /** 获取名片详情 */
  getDetail(cardId: string) {
    return api.get(`/api/card/detail/${cardId}`)
  },

  /** 创建/生成名片 */
  create(data: CardData) {
    return api.post('/api/card/generate', data)
  },

  /** AI 扫描名片（OCR + 结构化） */
  scan(imageUrl: string) {
    return api.post('/api/card/scan', { image_url: imageUrl })
  },
}

/* ========================================================================== */
/*  AI 智能匹配 API                                                            */
/* ========================================================================== */

export const matchApi = {
  /** 混合推荐（AI + 规则） */
  getHybridRecommend(cardId: string, params?: { limit?: number; page?: number }) {
    return api.post(`/api/v1/ai/recommend/hybrid/${cardId}`, params)
  },

  /** 获取匹配列表 */
  getMatches(params?: { page?: number; page_size?: number; type?: string }) {
    return api.get('/api/match/list', { data: params })
  },

  /** 解锁联系方式 */
  unlockContact(matchId: string, payment?: { method?: string }) {
    return api.post(`/api/match/unlock/${matchId}`, payment)
  },
}

/* ========================================================================== */
/*  人脉成长 API                                                               */
/* ========================================================================== */

export const growthApi = {
  /** 获取人脉指标（总人脉数、新增、活跃度等） */
  getMetrics() {
    return api.get('/api/growth/metrics')
  },

  /** 获取人脉增长趋势 */
  getTrends(params?: { days?: number; start_date?: string; end_date?: string }) {
    return api.get('/api/growth/trends', { data: params })
  },

  /** 获取人脉来源分布 */
  getSources() {
    return api.get('/api/growth/sources')
  },
}

/* ========================================================================== */
/*  定价与用量 API                                                             */
/* ========================================================================== */

export const pricingApi = {
  /** 获取所有套餐列表 */
  getPlans() {
    return api.get('/api/pricing/plans')
  },

  /** 获取当前用量 */
  getUsage() {
    return api.get('/api/pricing/usage')
  },

  /** 升级/变更套餐 */
  upgrade(planId: string, params?: { period?: 'month' | 'year' }) {
    return api.post(`/api/pricing/upgrade`, { plan_id: planId, ...params })
  },
}

/* ========================================================================== */
/*  支付 API                                                                   */
/* ========================================================================== */

export const paymentApi = {
  /** 微信支付统一下单 */
  wxPay(orderNo: string, params?: { openid?: string }) {
    return api.post('/api/payment/wxpay', { order_no: orderNo, ...params })
  },

  /** 获取订单列表 */
  getOrders(params?: { page?: number; page_size?: number; status?: string }) {
    return api.get('/api/payment/orders', { data: params })
  },
}

/* ========================================================================== */
/*  通知 API                                                                   */
/* ========================================================================== */

export const notificationApi = {
  /** 获取通知列表 */
  getList(params?: { page?: number; page_size?: number; unread_only?: boolean }) {
    return api.get('/api/notification/list', { data: params })
  },

  /** 标记通知已读 */
  markRead(notificationId: string) {
    return api.post(`/api/notification/read/${notificationId}`)
  },
}

/* ========================================================================== */
/*  应用市场 / 插件 API                                                        */
/* ========================================================================== */

export const appStoreApi = {
  /** 获取已安装/可用的插件列表 */
  getPlugins(params?: { category?: string; keyword?: string }) {
    return api.get('/api/appstore/plugins', { data: params })
  },

  /** 安装/启用插件 */
  install(pluginId: string) {
    return api.post(`/api/appstore/install`, { plugin_id: pluginId })
  },

  /** 获取应用排行榜 */
  getLeaderboard(params?: { category?: string; period?: 'weekly' | 'monthly' | 'all' }) {
    return api.get('/api/appstore/leaderboard', { data: params })
  },
}

export default {
  authApi,
  cardApi,
  matchApi,
  growthApi,
  pricingApi,
  paymentApi,
  notificationApi,
  appStoreApi,
}
