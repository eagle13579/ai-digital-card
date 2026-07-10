/**
 * 三通道账单 — AI数智名片 适配器
 * ============================================
 * 源Feature: feature_triple_channel_billing (三通道账单)
 * 版本:      1.0.0
 * 注入日期:  2026-07-09
 *
 * 核心能力:
 *   基于知识查询双通道与Token极致效率机制，精细化追踪和控制Token消耗与知识查询成本
 *   三通道: A(高精度/RAG) / B(快速/SAG) / C(批量/LLM回退)
 *
 * 集成点:
 *   1. AI对话 (pages/ai/chat/) → 追踪RAG查询命中率 + Token消耗
 *   2. AI内容生成 (pages/ai/generate/) → 追踪SAG生成Token
 *   3. 名片扫描 / 智能匹配 → LLM回退追踪
 *   4. AI数据洞察 → 账单汇总展示
 *
 * 用法:
 *   const billing = require('../../features/triple-channel-billing-adapter')
 *   // 记录一次RAG命中
 *   billing.countRagHits('channel_a', 3, { query: '...', tokens: 450 })
 *   // 追踪SAG Token消耗
 *   billing.trackSagTokens(320, { model: 'deepseek-sag', prompt: '...' })
 *   // 追踪LLM回退
 *   billing.trackLlmFallback('rag_timeout', { query: '...', tokens: 1200 })
 *   // 获取当前账单
 *   const bill = billing.getBill()
 */

const CONFIG = {
  channel_a_budget: 1000000,   // 通道A (高精度/RAG) 每日Token预算
  channel_b_budget: 5000000,   // 通道B (快速/SAG) 每日Token预算
  channel_c_budget: 10000000,  // 通道C (批量/LLM回退) 每日Token预算
  alert_threshold: 0.85,       // 费用告警阈值 (占预算百分比)
  billing_cycle: 'daily',      // 账单周期: daily | weekly | monthly
}

/**
 * 三通道账单状态（内存中累计）
 * 各通道按 token_usage / hits / cost 三个维度追踪
 */
const Channels = {
  /** 通道A — 高精度 RAG 查询通道 */
  channel_a: {
    name: '高精度RAG通道',
    token_usage: 0,       // 已消耗Token数
    hits: 0,              // RAG查询命中次数
    misses: 0,            // RAG查询未命中次数
    cost: 0,              // 累计成本（单位：分）
    records: [],          // 明细记录
  },
  /** 通道B — 快速 SAG 自注意力生成通道 */
  channel_b: {
    name: '快速SAG通道',
    token_usage: 0,       // 已消耗Token数
    sessions: 0,          // SAG生成会话数
    cost: 0,              // 累计成本
    records: [],
  },
  /** 通道C — 批量/LLM回退通道 */
  channel_c: {
    name: '批量LLM回退通道',
    token_usage: 0,       // 已消耗Token数
    fallbacks: 0,         // 回退次数
    cost: 0,              // 累计成本
    records: [],
  },
}

/** 费率表 (分/千Token) */
const RATES = {
  channel_a: 0.15,   // RAG 检索 + 精排
  channel_b: 0.08,   // SAG 自注意力生成（优化费率）
  channel_c: 0.25,   // 完整LLM回退（标准费率）
}

/** 账单累积器 — 跨周期统计 */
let billingState = {
  cycles: [],           // 历史周期快照
  cycleStart: Date.now(),
  alerts: [],           // 告警记录
  globalFallbackCount: 0,
}

// =============================================================================
//  核心追踪方法
// =============================================================================

/**
 * 计数RAG查询命中/未命中（通道A — 高精度知识查询）
 * @param {string} channel     通道标识: 'channel_a'
 * @param {number} hitCount    命中次数（正数=命中, 负数=未命中, 0=仅记录）
 * @param {object} [meta]      附带元数据
 * @param {string} [meta.query]      查询文本(摘要)
 * @param {number} [meta.tokens]     本次消耗Token数
 * @param {number} [meta.latency]    查询延迟ms
 * @returns {object} 通道A当前状态
 */
function countRagHits(channel, hitCount = 1, meta = {}) {
  if (channel !== 'channel_a') {
    console.warn(`[TripleBilling] countRagHits 仅支持 channel_a，收到: ${channel}`)
    return getChannelSnapshot('channel_a')
  }

  const ch = Channels.channel_a
  const { query = '', tokens = 0, latency = 0 } = meta || {}

  if (hitCount > 0) {
    ch.hits += hitCount
  } else if (hitCount < 0) {
    ch.misses += Math.abs(hitCount)
  }

  if (tokens > 0) {
    ch.token_usage += tokens
    ch.cost += (tokens / 1000) * RATES.channel_a
  }

  ch.records.push({
    type: hitCount > 0 ? 'hit' : (hitCount < 0 ? 'miss' : 'record'),
    hitCount,
    tokens,
    latency,
    query: query.substring(0, 100),
    timestamp: new Date().toISOString(),
  })

  // 限制记录长度
  if (ch.records.length > 500) ch.records = ch.records.slice(-500)

  checkAlert('channel_a')
  return getChannelSnapshot('channel_a')
}

/**
 * 追踪SAG Token消耗（通道B — 快速自注意力生成）
 * @param {number} tokens      消耗的Token数
 * @param {object} [meta]      附带元数据
 * @param {string} [meta.model]      使用的模型
 * @param {string} [meta.prompt]     提示词摘要
 * @param {number} [meta.generated]  生成了多少Token
 * @returns {object} 通道B当前状态
 */
function trackSagTokens(tokens, meta = {}) {
  if (typeof tokens !== 'number' || tokens <= 0) {
    return { success: false, message: 'Token数必须为正整数', channel: getChannelSnapshot('channel_b') }
  }

  const ch = Channels.channel_b
  const { model = 'sag-default', prompt = '', generated = 0 } = meta || {}

  ch.token_usage += tokens
  ch.sessions += 1
  ch.cost += (tokens / 1000) * RATES.channel_b

  ch.records.push({
    tokens,
    model: model.substring(0, 50),
    prompt: prompt.substring(0, 100),
    generated,
    cost: (tokens / 1000) * RATES.channel_b,
    timestamp: new Date().toISOString(),
  })

  if (ch.records.length > 500) ch.records = ch.records.slice(-500)

  checkAlert('channel_b')
  return getChannelSnapshot('channel_b')
}

/**
 * 追踪LLM回退事件（通道C — 批量/标准LLM回退）
 * 当SAG/RAG无法满足需求时，回退到完整LLM调用
 * @param {string} reason       回退原因标识
 * @param {object} [meta]       附带元数据
 * @param {string} [meta.query]      原始查询
 * @param {number} [meta.tokens]     回退消耗Token数
 * @param {string} [meta.source]     来源通道 (channel_a | channel_b)
 * @returns {object} 通道C当前状态
 */
function trackLlmFallback(reason, meta = {}) {
  const ch = Channels.channel_c
  const { query = '', tokens = 0, source = 'unknown' } = meta || {}

  ch.fallbacks += 1
  billingState.globalFallbackCount += 1

  if (tokens > 0) {
    ch.token_usage += tokens
    ch.cost += (tokens / 1000) * RATES.channel_c
  }

  ch.records.push({
    reason: reason || 'unknown',
    source,
    tokens,
    query: query.substring(0, 100),
    cost: tokens > 0 ? (tokens / 1000) * RATES.channel_c : 0,
    timestamp: new Date().toISOString(),
  })

  if (ch.records.length > 500) ch.records = ch.records.slice(-500)

  checkAlert('channel_c')
  return getChannelSnapshot('channel_c')
}

// =============================================================================
//  账单查询
// =============================================================================

/**
 * 获取三通道账单汇总
 * @param {object} [options]  查询选项
 * @param {boolean} [options.detail=false]  是否包含明细记录
 * @returns {object} 完整账单
 */
function getBill(options = {}) {
  const { detail = false } = options || {}

  const now = Date.now()
  const elapsed = now - billingState.cycleStart

  const channels = {}
  for (const [key, ch] of Object.entries(Channels)) {
    channels[key] = getChannelSnapshot(key, detail)
  }

  const totalUsage = channels.channel_a.token_usage + channels.channel_b.token_usage + channels.channel_c.token_usage
  const totalCost = channels.channel_a.cost + channels.channel_b.cost + channels.channel_c.cost
  const totalBudget = CONFIG.channel_a_budget + CONFIG.channel_b_budget + CONFIG.channel_c_budget
  const usagePercent = totalBudget > 0 ? Math.round((totalUsage / totalBudget) * 10000) / 100 : 0

  const alerts = getAlerts()

  const bill = {
    summary: {
      total_tokens: totalUsage,
      total_cost: Math.round(totalCost * 100) / 100,
      total_budget: totalBudget,
      usage_percent: usagePercent,
      cycle: CONFIG.billing_cycle,
      cycle_started: new Date(billingState.cycleStart).toISOString(),
      alert_count: alerts.length,
      alerts_triggered: alerts.length > 0,
    },
    channels,
    fallback_stats: {
      total_fallbacks: billingState.globalFallbackCount,
      channel_c_fallbacks: Channels.channel_c.fallbacks,
    },
    config: { ...CONFIG },
    alerts,
    timestamp: new Date().toISOString(),
  }

  return bill
}

/**
 * 获取特定通道快照
 * @param {string} channelKey   通道标识
 * @param {boolean} [includeRecords=false]  是否包含记录
 * @returns {object}
 */
function getChannelSnapshot(channelKey, includeRecords = false) {
  const ch = Channels[channelKey]
  if (!ch) return null

  const budgetMap = {
    channel_a: CONFIG.channel_a_budget,
    channel_b: CONFIG.channel_b_budget,
    channel_c: CONFIG.channel_c_budget,
  }
  const budget = budgetMap[channelKey] || 0

  const snapshot = {
    name: ch.name,
    token_usage: ch.token_usage,
    cost: Math.round(ch.cost * 100) / 100,
    budget,
    usage_percent: budget > 0 ? Math.round((ch.token_usage / budget) * 10000) / 100 : 0,
    rate: RATES[channelKey],
  }

  // 通道特定字段
  if (channelKey === 'channel_a') {
    snapshot.hits = ch.hits
    snapshot.misses = ch.misses
    snapshot.hit_rate = (ch.hits + ch.misses) > 0
      ? Math.round((ch.hits / (ch.hits + ch.misses)) * 10000) / 100
      : 0
  } else if (channelKey === 'channel_b') {
    snapshot.sessions = ch.sessions
    snapshot.avg_tokens_per_session = ch.sessions > 0 ? Math.round(ch.token_usage / ch.sessions) : 0
  } else if (channelKey === 'channel_c') {
    snapshot.fallbacks = ch.fallbacks
  }

  if (includeRecords) {
    snapshot.recent_records = ch.records.slice(-20)
  }

  return snapshot
}

// =============================================================================
//  告警系统
// =============================================================================

/** 检查通道是否超过告警阈值 */
function checkAlert(channelKey) {
  const budgetMap = {
    channel_a: CONFIG.channel_a_budget,
    channel_b: CONFIG.channel_b_budget,
    channel_c: CONFIG.channel_c_budget,
  }
  const budget = budgetMap[channelKey] || 0
  const usage = Channels[channelKey]?.token_usage || 0

  if (budget <= 0) return

  const percent = usage / budget
  if (percent >= CONFIG.alert_threshold) {
    // 避免重复告警（同一周期内同一通道仅告警一次）
    const existing = billingState.alerts.find(
      a => a.channel === channelKey && a.cycle_started === billingState.cycleStart
    )
    if (!existing) {
      const alert = {
        channel: channelKey,
        channel_name: Channels[channelKey]?.name || channelKey,
        usage,
        budget,
        percent: Math.round(percent * 10000) / 100,
        threshold: CONFIG.alert_threshold,
        message: `⚠️ ${Channels[channelKey]?.name || channelKey} 使用量已达预算 ${Math.round(percent * 100)}% (${usage}/${budget} Token)`,
        timestamp: new Date().toISOString(),
        cycle_started: billingState.cycleStart,
      }
      billingState.alerts.push(alert)
      console.warn(`[TripleBilling] ${alert.message}`)
    }
  }
}

/** 获取未处理的告警列表 */
function getAlerts() {
  return billingState.alerts.map(a => ({
    channel: a.channel,
    channel_name: a.channel_name,
    percent: a.percent,
    message: a.message,
    timestamp: a.timestamp,
  }))
}

/** 清除已处理的告警 */
function clearAlerts() {
  billingState.alerts = []
  return { cleared: true }
}

// =============================================================================
//  周期管理
// =============================================================================

/** 重置账单周期（每日/每周/每月轮换时调用） */
function resetCycle() {
  // 保存当前周期快照
  billingState.cycles.push({
    summary: getBill({ detail: false }).summary,
    snapshot: {
      channel_a: { ...Channels.channel_a, records: [] },
      channel_b: { ...Channels.channel_b, records: [] },
      channel_c: { ...Channels.channel_c, records: [] },
    },
    ended_at: new Date().toISOString(),
  })

  // 限制历史周期数
  if (billingState.cycles.length > 30) {
    billingState.cycles = billingState.cycles.slice(-30)
  }

  // 重置各通道计数器（保留记录结构）
  for (const key of Object.keys(Channels)) {
    Channels[key].token_usage = 0
    Channels[key].cost = 0
    if (key === 'channel_a') { Channels[key].hits = 0; Channels[key].misses = 0 }
    if (key === 'channel_b') Channels[key].sessions = 0
    if (key === 'channel_c') Channels[key].fallbacks = 0
    Channels[key].records = []
  }

  billingState.cycleStart = Date.now()
  billingState.alerts = []

  return { success: true, newCycleStarted: new Date(billingState.cycleStart).toISOString() }
}

/** 获取历史周期数据 */
function getCycleHistory(limit = 10) {
  return billingState.cycles.slice(-limit)
}

// =============================================================================
//  配置 & 实用工具
// =============================================================================

/**
 * 更新配置
 * @param {object} newConfig 配置覆盖
 */
function updateConfig(newConfig) {
  if (!newConfig || typeof newConfig !== 'object') return

  const validKeys = Object.keys(CONFIG)
  for (const [key, value] of Object.entries(newConfig)) {
    if (validKeys.includes(key)) {
      CONFIG[key] = value
    }
  }

  return { ...CONFIG }
}

/** 获取当前费率表 */
function getRates() {
  return { ...RATES }
}

/**
 * 更新费率（谨慎使用）
 * @param {object} newRates 费率覆盖 { channel_a, channel_b, channel_c }
 */
function updateRates(newRates) {
  if (!newRates || typeof newRates !== 'object') return
  for (const [key, value] of Object.entries(newRates)) {
    if (RATES[key] !== undefined && typeof value === 'number' && value > 0) {
      RATES[key] = value
    }
  }
  return { ...RATES }
}

/** 总览统计 */
function getOverview() {
  const bill = getBill()
  return {
    channels: {
      channel_a: {
        hit_rate: bill.channels.channel_a.hit_rate,
        tokens: bill.channels.channel_a.token_usage,
      },
      channel_b: {
        sessions: bill.channels.channel_b.sessions,
        tokens: bill.channels.channel_b.token_usage,
        avg_per_session: bill.channels.channel_b.avg_tokens_per_session,
      },
      channel_c: {
        fallbacks: bill.channels.channel_c.fallbacks,
        tokens: bill.channels.channel_c.token_usage,
      },
    },
    total_tokens: bill.summary.total_tokens,
    total_cost: bill.summary.total_cost,
    usage_percent: bill.summary.usage_percent,
    alerts_active: bill.summary.alert_count,
  }
}

// =============================================================================
//  导出 API
// =============================================================================
module.exports = {
  // Feature 信息
  featureName: '三通道账单',
  featureVersion: '1.0.0',
  featureDomain: 'cognitive',

  // 配置
  CONFIG,
  updateConfig,

  // 核心追踪方法
  countRagHits,
  trackSagTokens,
  trackLlmFallback,

  // 账单查询
  getBill,
  getOverview,

  // 通道查询
  getChannel: getChannelSnapshot,
  getRates,
  updateRates,

  // 周期管理
  resetCycle,
  getCycleHistory,

  // 告警
  getAlerts,
  clearAlerts,
}
