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
 *   graphApi     — 人脉图谱
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

/* ========================================================================== */
/*  AI 质量评分 API                                                           */
/* ========================================================================== */

export interface OptimizationResult {
  overall_score: number
  completeness: number
  keyword_coverage: number
  professionalism: number
  top_priorities: string[]
}

export const optimizeApi = {
  /** 获取名片质量评分与优化建议 */
  getOptimization(brochureId: number, industry?: string) {
    return api.get<OptimizationResult>(
      `/api/v1/ai/assist/optimize/${brochureId}`,
      { data: { industry } },
    )
  },
}

/* ========================================================================== */
/*  AI 写作助手 API                                                           */
/* ========================================================================== */

export interface WriteParams {
  purpose: string
  name: string
  position: string
  company: string
  industry: string
  skills: string
  description: string
  highlights: string
}

export interface WriteResult {
  purpose: string
  content: string
}

export const writeApi = {
  /** AI 生成文案（介绍、摘要、宣传语等） */
  generateCopy(params: WriteParams) {
    return api.post<WriteResult>('/api/v1/ai/assist/write', params)
  },
}

/* ========================================================================== */
/*  AI 语义搜索 API                                                           */
/* ========================================================================== */

export interface SearchParams {
  query: string
  top_k?: number
  min_score?: number
}

export interface SearchResultItem {
  id: string
  score: number
  content: string
  [key: string]: any
}

export const searchApi = {
  /** 语义搜索（基于向量相似度） */
  semanticSearch(params: SearchParams) {
    return api.post<SearchResultItem[]>('/api/v1/match/semantic-search', params)
  },
}

/* ========================================================================== */
/*  AI SAG 增强 API                                                           */
/* ========================================================================== */

export interface SagParams {
  mode: string
  content: string
  depth?: number
}

export interface SagResult {
  conclusion: string
  confidence: number
  score: number
  suggestions: string[]
}

export const sagApi = {
  /** SAG 增强分析（场景/意图/生成分析） */
  analyze(params: SagParams) {
    return api.post<SagResult>('/api/v1/ai/sag/analyze', params)
  },
}

/* ========================================================================== */
/*  知识图谱 API                                                               */
/* ========================================================================== */

export interface GraphNode {
  id: string
  label: string
  type: 'person' | 'company' | 'industry' | 'tag' | 'location'
  /** 是否是当前用户/中心节点 */
  isCenter?: boolean
  company?: string
  avatar?: string
  match_score?: number
  /** 连接数（用于计算节点大小） */
  connectionCount?: number
  [key: string]: any
}

export interface GraphEdge {
  source: string
  target: string
  relation: 'works_at' | 'tagged_as' | 'matched' | 'trusted' | 'same_industry' | 'same_company' | 'same_location'
  weight?: number
  label?: string
  [key: string]: any
}

export interface GraphData {
  central: { id: string; label: string; type: string; [key: string]: any }
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export const graphApi = {
  /** 获取用户人脉网络图谱数据 */
  getNetwork(userId: number | string, depth: number = 2) {
    return api.get<GraphData>(`/api/v1/knowledge-graph/network/${userId}`, { data: { depth } })
  },
  /** 获取用户图谱洞察分析 */
  getInsights(userId: number | string) {
    return api.get(`/api/v1/knowledge-graph/insights/${userId}`)
  },
}

/* ========================================================================== */
/*  用量 API                                                                   */
/* ========================================================================== */

export const usageApi = {
  /** 获取当前用户AI用量 */
  getMyUsage() {
    return api.get('/api/v1/usage')
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
  optimizeApi,
  writeApi,
  searchApi,
  sagApi,
  graphApi,
  usageApi,
}


/* ==============================================================
 *  AI 对话 API (新增 — P0 AI注入)
 * ============================================================== */

/** AI对话请求参数 */
export interface ChatRequest {
  messages: { role: 'user' | 'assistant'; content: string }[]
  model?: string
  temperature?: number
  max_tokens?: number
}

/** AI对话响应 */
export interface ChatResponse {
  reply: string
  model: string
  usage?: { prompt_tokens: number; completion_tokens: number }
}

/** DeepSeek直接对话请求 */
export interface DeepSeekRequest {
  prompt: string
  model?: string
  temperature?: number
}

export const chatApi = {
  /** AI智能对话 */
  sendMessage(data: ChatRequest) {
    return api.post<ChatResponse>('/api/v1/ai/chat', { data })
  },
}

export const deepseekApi = {
  /** DeepSeek 直接对话 */
  chat(data: DeepSeekRequest) {
    return api.post<ChatResponse>('/api/v1/ai/deepseek/chat', { data })
  },
  /** DeepSeek 文本生成 */
  generate(prompt: string) {
    return api.post<{ content: string }>('/api/v1/ai/deepseek/generate', { data: { prompt } })
  },
}

/* ==============================================================
 *  AI 管线 API (新增)
 * ============================================================== */

export interface PipelineQuery {
  query: string
  mode?: 'rag' | 'sag' | 'hybrid'
}

export const pipelineApi = {
  /** 混合查询 (RAG+SAG) */
  hybridQuery(data: PipelineQuery) {
    return api.post<{ result: string; sources: string[] }>('/api/v1/ai/hybrid/query', { data })
  },
  /** 管线状态 */
  pipelineStatus() {
    return api.get<{ status: string; last_run: string }>('/api/v1/ai/pipeline/status')
  },
}

/* ==============================================================
 *  AI 知识图谱 API (新增)
 * ============================================================== */

export interface GraphNode {
  id: string
  label: string
  type: string
  weight: number
}

export interface GraphEdge {
  source: string
  target: string
  label: string
  weight: number
}

export interface KnowledgeGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export const knowledgeGraphApi = {
  /** 获取用户知识图谱 */
  getGraph(userId?: number) {
    const url = userId ? `/api/v1/knowledge-graph?user_id=${userId}` : '/api/v1/knowledge-graph'
    return api.get<KnowledgeGraph>(url)
  },
}
