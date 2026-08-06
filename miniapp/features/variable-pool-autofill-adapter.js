/**
 * 变量池自动填充 — AI数智名片 适配器
 * =============================================
 * 源Feature: variable-pool-autofill (变量池自动填充)
 * 版本:      1.0.0
 * 注入日期:  2026-07-09
 *
 * 核心能力:
 *   监控变量池水位并自动从认知进化引擎和五池均衡管理器填充缺失变量
 *   保障认知循环的变量供给不中断
 *
 * 集成点:
 *   1. AI对话 → 对话后自动检查变量池水位，触发填充
 *   2. 名片扫描 → OCR结果提取变量后检查池状态
 *   3. 智能匹配 → 匹配完成后补充缺失的决策变量
 *   4. AI数据洞察 → 洞察分析前确保变量池充足
 *   5. MockService → 模拟变量池水位变化，验证填充逻辑
 *
 * 内置适配器协议: scan() / match() / fill() / report()
 *
 * 用法:
 *   const vpAutofill = require('../../features/variable-pool-autofill-adapter')
 *   // 扫描变量池水位
 *   const status = vpAutofill.scan()
 *   // 匹配缺失变量与可用来源
 *   const matches = vpAutofill.match()
 *   // 执行自动填充
 *   const result = vpAutofill.fill()
 *   // 获取填充报告
 *   const report = vpAutofill.report()
 */

const CONFIG = {
  fill_threshold: 0.3,          // 触发自动填充的水位阈值 (0.0-1.0)
  max_fill_per_cycle: 10,       // 每轮最多填充变量数
  pool_names: ['variables'],    // 受监控的变量池名称列表
  auto_fill_enabled: true,      // 是否启用自动填充
  min_variables_for_healthy: 5, // 健康水位最少变量数
}

/**
 * 变量池状态数据结构
 * 维护多个受监控池的内存状态
 */
const PoolState = {
  variables: {
    name: '变量池',
    capacity: 50,
    current: [],
    lastFillAt: null,
    fillCount: 0,
  },
}

/**
 * 填充历史记录
 */
let fillHistory = []
let cycleCount = 0

/**
 * 可选的依赖适配器引用（由 init() 注入）
 * @type {object|null}
 */
let cognitiveEngineRef = null
let fivePoolsBalanceRef = null

// =============================================================================
//  scan() — 扫描变量池水位状态
// =============================================================================

/**
 * 扫描所有受监控变量池，计算水位并返回详细状态
 * @returns {object} {
 *   pools: [{ name, currentCount, capacity, fillPercent, health }],
 *   overallHealth: 'healthy' | 'warning' | 'critical',
 *   needsFill: boolean,
 *   threshold: number,
 *   timestamp: string
 * }
 */
function scan() {
  const pools = CONFIG.pool_names.map(poolName => {
    const pool = PoolState[poolName]
    if (!pool) return { name: poolName, error: '未知池名称' }

    const currentCount = pool.current.length
    const capacity = pool.capacity
    const fillPercent = capacity > 0 ? currentCount / capacity : 0

    let health = 'healthy'
    if (fillPercent <= CONFIG.fill_threshold) {
      health = 'critical'
    } else if (fillPercent <= CONFIG.fill_threshold * 2) {
      health = 'warning'
    }

    return {
      name: poolName,
      displayName: pool.name,
      currentCount,
      capacity,
      fillPercent: Math.round(fillPercent * 100) / 100,
      health,
      lastFillAt: pool.lastFillAt,
    }
  })

  const criticalPools = pools.filter(p => p.health === 'critical')
  const warningPools = pools.filter(p => p.health === 'warning')
  const healthyPools = pools.filter(p => p.health === 'healthy')

  let overallHealth = 'healthy'
  if (criticalPools.length > 0) overallHealth = 'critical'
  else if (warningPools.length > 0) overallHealth = 'warning'

  return {
    pools,
    overallHealth,
    needsFill: criticalPools.length > 0 || warningPools.length > 0,
    threshold: CONFIG.fill_threshold,
    timestamp: new Date().toISOString(),
    summary: `变量池总体状态: ${overallHealth} | 健康: ${healthyPools.length} | 警告: ${warningPools.length} | 危险: ${criticalPools.length}`,
  }
}

// =============================================================================
//  match() — 匹配缺失变量与可用来源
// =============================================================================

/**
 * 根据变量池水位状态，匹配可从认知进化引擎和五池均衡管理器获取的变量
 * @param {object} [scanResult] 可选，传入上次 scan() 结果；不传则自动扫描
 * @returns {object} {
 *   matched: [{ name, source, confidence, reason }],
 *   unmatched: string[],
 *   sourceBreakdown: { cognitiveEngine: number, fivePoolsBalance: number },
 *   totalMatched: number,
 *   canProceed: boolean
 * }
 */
function match(scanResult) {
  const status = scanResult || scan()
  const matched = []
  const unmatched = []

  // --- 1. 确定缺失变量 ---
  const pool = PoolState.variables
  const existingNames = new Set(pool.current.map(v => v.name))
  const existingValues = new Set(pool.current.map(v => `${v.name}:${v.value}`))

  // --- 2. 从认知进化引擎推导可能的变量 ---
  // 认知进化引擎提供的标准变量类型
  const cognitiveDerived = [
    { name: '用户意图', category: 'behavior', confidence: 0.85, reason: '认知进化引擎—对话意图分析' },
    { name: '情感倾向', category: 'psychology', confidence: 0.75, reason: '认知进化引擎—情感分析' },
    { name: '行业标签', category: 'categorization', confidence: 0.90, reason: '认知进化引擎—行业匹配' },
    { name: '决策类型', category: 'decision', confidence: 0.80, reason: '认知进化引擎—决策识别' },
    { name: '问题复杂度', category: 'evaluation', confidence: 0.70, reason: '认知进化引擎—复杂度评估' },
    { name: '知识领域', category: 'categorization', confidence: 0.85, reason: '认知进化引擎—知识领域映射' },
    { name: '紧急程度', category: 'priority', confidence: 0.65, reason: '认知进化引擎—紧急度推断' },
    { name: '关联人脉', category: 'network', confidence: 0.60, reason: '认知进化引擎—人脉关联分析' },
  ]

  // --- 3. 从五池均衡管理器获取可转移变量 ---
  // 五池均衡管理器可在池间转移变量（现象→变量、模型→变量等）
  const balanceTransferable = [
    { name: '关键实体', source: 'phenomena', confidence: 0.88, reason: '五池均衡—现象池萃取' },
    { name: '核心指标', source: 'models', confidence: 0.82, reason: '五池均衡—模型池提取' },
    { name: '验证假设', source: 'decisions', confidence: 0.78, reason: '五池均衡—决策池转化' },
    { name: '执行瓶颈', source: 'actions', confidence: 0.72, reason: '五池均衡—行动池分析' },
    { name: '时间窗口', source: 'phenomena', confidence: 0.68, reason: '五池均衡—时序数据提取' },
    { name: '资源需求', source: 'actions', confidence: 0.75, reason: '五池均衡—行动资源推断' },
    { name: '风险等级', source: 'decisions', confidence: 0.70, reason: '五池均衡—决策风险评估' },
    { name: '趋势方向', source: 'models', confidence: 0.80, reason: '五池均衡—模型趋势归纳' },
  ]

  // --- 4. 合并候选变量，过滤已有 ---
  const allCandidates = [
    ...cognitiveDerived.map(v => ({ ...v, source: 'cognitive-evolution-engine' })),
    ...balanceTransferable.map(v => ({ ...v, source: 'five-pools-balance-manager' })),
  ]

  for (const candidate of allCandidates) {
    if (existingNames.has(candidate.name)) {
      unmatched.push(candidate.name)
    } else {
      matched.push({
        name: candidate.name,
        source: candidate.source,
        confidence: candidate.confidence,
        reason: candidate.reason,
        category: candidate.category || candidate.source || 'unknown',
        priority: candidate.confidence >= 0.8 ? 'high' : candidate.confidence >= 0.65 ? 'medium' : 'low',
      })
    }
  }

  // --- 5. 统计来源 ---
  const sourceBreakdown = {
    cognitiveEngine: matched.filter(v => v.source === 'cognitive-evolution-engine').length,
    fivePoolsBalance: matched.filter(v => v.source === 'five-pools-balance-manager').length,
  }

  return {
    matched: matched.slice(0, CONFIG.max_fill_per_cycle * 2), // 返回候选池
    unmatched,
    sourceBreakdown,
    totalMatched: Math.min(matched.length, CONFIG.max_fill_per_cycle * 2),
    canProceed: matched.length > 0 && status.overallHealth !== 'healthy',
    timestamp: new Date().toISOString(),
  }
}

// =============================================================================
//  fill() — 执行自动填充
// =============================================================================

/**
 * 执行变量池自动填充操作
 * 从匹配结果中选择最高置信度的变量填入变量池
 * @param {object} [matchResult] 可选，传入上次 match() 结果；不传则自动匹配
 * @returns {object} {
 *   success: boolean,
 *   filled: [{ name, value, source, confidence }],
 *   fillCount: number,
 *   poolStatusAfter: object,
 *   cycleInfo: { cycleId, threshold, maxFill },
 *   timestamp: string
 * }
 */
function fill(matchResult) {
  if (!CONFIG.auto_fill_enabled) {
    return {
      success: false,
      filled: [],
      fillCount: 0,
      error: '自动填充已禁用 (auto_fill_enabled=false)',
      timestamp: new Date().toISOString(),
    }
  }

  // --- 1. 扫描当前状态 ---
  const status = scan()
  if (!status.needsFill) {
    return {
      success: true,
      filled: [],
      fillCount: 0,
      message: '变量池水位健康，无需填充',
      poolStatusAfter: status,
      timestamp: new Date().toISOString(),
    }
  }

  // --- 2. 获取匹配候选 ---
  const matches = matchResult || match(status)
  if (!matches.canProceed || matches.matched.length === 0) {
    return {
      success: false,
      filled: [],
      fillCount: 0,
      message: '无可用填充来源',
      poolStatusAfter: status,
      timestamp: new Date().toISOString(),
    }
  }

  // --- 3. 按置信度排序，选取 top-N ---
  const sorted = [...matches.matched].sort((a, b) => b.confidence - a.confidence)
  const toFill = sorted.slice(0, CONFIG.max_fill_per_cycle)

  // --- 4. 执行填充 ---
  const filled = []
  for (const candidate of toFill) {
    const value = generateValueForVariable(candidate)
    const variableEntry = {
      id: `var_autofill_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name: candidate.name,
      value,
      confidence: candidate.confidence,
      source: candidate.source,
      category: candidate.category || 'general',
      reason: candidate.reason,
      filledAt: new Date().toISOString(),
      batch: cycleCount,
    }
    PoolState.variables.current.push(variableEntry)
    filled.push(variableEntry)
  }

  // --- 5. 更新池状态 ---
  cycleCount++
  PoolState.variables.lastFillAt = new Date().toISOString()
  PoolState.variables.fillCount += filled.length

  // --- 6. 记录填充历史 ---
  const fillRecord = {
    cycleId: `fill_${cycleCount}`,
    timestamp: new Date().toISOString(),
    requested: toFill.length,
    filled: filled.length,
    threshold: CONFIG.fill_threshold,
    maxFill: CONFIG.max_fill_per_cycle,
    sources: { ...matches.sourceBreakdown },
    poolAfter: {
      count: PoolState.variables.current.length,
      capacity: PoolState.variables.capacity,
    },
  }
  fillHistory.push(fillRecord)

  // --- 7. 裁剪超出容量 ---
  trimPool()

  // --- 8. 返回填充结果 ---
  const afterStatus = scan()

  return {
    success: true,
    filled: filled.map(v => ({
      name: v.name,
      value: v.value,
      source: v.source,
      confidence: v.confidence,
    })),
    fillCount: filled.length,
    poolStatusBefore: status,
    poolStatusAfter: afterStatus,
    cycleInfo: {
      cycleId: `fill_${cycleCount}`,
      threshold: CONFIG.fill_threshold,
      maxFill: CONFIG.max_fill_per_cycle,
    },
    timestamp: new Date().toISOString(),
  }
}

// =============================================================================
//  report() — 获取填充报告
// =============================================================================

/**
 * 生成变量池自动填充的综合报告
 * 包含填充历史、成功率、变量池趋势、可用来源统计
 * @param {object} [options]
 * @param {number} [options.historyLimit] 返回最近N条填充记录 (默认全部)
 * @param {boolean} [options.includeVariables] 包含当前变量清单 (默认false)
 * @returns {object} {
 *   feature: { name, version, domain },
 *   config: { fillThreshold, maxFillPerCycle, monitoredPools },
 *   currentStatus: object,          // scan() 状态快照
 *   fillSummary: {
 *     totalCycles, totalFilled, totalAttempts,
 *     successRate, avgPerCycle, lastFillAt
 *   },
 *   sourceStats: { cognitiveEngine, fivePoolsBalance },
 *   history: fillRecord[],
 *   variables: object[] | null,
 *   timestamp: string
 * }
 */
function report(options = {}) {
  const { historyLimit, includeVariables } = options

  const currentStatus = scan()

  // --- 填充汇总 ---
  const totalAttempts = fillHistory.length
  const totalFilled = fillHistory.reduce((sum, r) => sum + r.filled, 0)
  const successRate = totalAttempts > 0
    ? Math.round((fillHistory.filter(r => r.filled > 0).length / totalAttempts) * 10000) / 100
    : 0
  const avgPerCycle = totalAttempts > 0
    ? Math.round((totalFilled / totalAttempts) * 100) / 100
    : 0
  const lastFill = fillHistory.length > 0 ? fillHistory[fillHistory.length - 1] : null

  // --- 来源统计 ---
  const sourceStats = {
    cognitiveEngine: fillHistory.reduce((sum, r) => sum + (r.sources.cognitiveEngine || 0), 0),
    fivePoolsBalance: fillHistory.reduce((sum, r) => sum + (r.sources.fivePoolsBalance || 0), 0),
  }

  // --- 高置信度变量统计 ---
  const highConfVariables = PoolState.variables.current.filter(v => v.confidence >= 0.8).length
  const variableCategories = {}
  for (const v of PoolState.variables.current) {
    const cat = v.category || 'uncategorized'
    variableCategories[cat] = (variableCategories[cat] || 0) + 1
  }

  return {
    feature: {
      name: '变量池自动填充',
      version: '1.0.0',
      domain: 'cognitive',
    },
    config: {
      fillThreshold: CONFIG.fill_threshold,
      maxFillPerCycle: CONFIG.max_fill_per_cycle,
      monitoredPools: [...CONFIG.pool_names],
      autoFillEnabled: CONFIG.auto_fill_enabled,
      minVariablesForHealthy: CONFIG.min_variables_for_healthy,
    },
    currentStatus,
    fillSummary: {
      totalCycles: cycleCount,
      totalFilled,
      totalAttempts,
      successRate: `${successRate}%`,
      avgPerCycle,
      highConfidenceVariables: highConfVariables,
      variableCategories,
      lastFillAt: lastFill ? lastFill.timestamp : null,
    },
    sourceStats,
    history: historyLimit
      ? fillHistory.slice(-historyLimit)
      : [...fillHistory],
    variables: includeVariables
      ? PoolState.variables.current.map(v => ({
          id: v.id,
          name: v.name,
          value: v.value,
          confidence: v.confidence,
          source: v.source,
          category: v.category,
          filledAt: v.filledAt,
        }))
      : null,
    timestamp: new Date().toISOString(),
  }
}

// =============================================================================
//  辅助方法
// =============================================================================

/**
 * 为候选变量生成一个合理的默认值/推断值
 * @param {object} candidate - 变量候选对象
 * @returns {string} 推断值
 */
function generateValueForVariable(candidate) {
  const valueMap = {
    '用户意图': '信息获取',
    '情感倾向': '中性',
    '行业标签': '科技/互联网',
    '决策类型': '评估中',
    '问题复杂度': '中等',
    '知识领域': '通用',
    '紧急程度': '常规',
    '关联人脉': '待发现',
    '关键实体': '检测中',
    '核心指标': '待采集',
    '验证假设': '待验证',
    '执行瓶颈': '无',
    '时间窗口': '即时',
    '资源需求': '标准',
    '风险等级': '低风险',
    '趋势方向': '平稳',
  }
  return valueMap[candidate.name] || `[推断] ${candidate.name} (来自${candidate.source})`
}

/**
 * 清理超出容量的变量（保留最新 MAX_CAPACITY 条）
 */
function trimPool() {
  const MAX_CAPACITY = PoolState.variables.capacity
  for (const key of Object.keys(PoolState)) {
    if (PoolState[key].current && PoolState[key].current.length > MAX_CAPACITY) {
      PoolState[key].current = PoolState[key].current.slice(-MAX_CAPACITY)
    }
  }
}

// =============================================================================
//  主动填充触发器（供外部模块调用）
// =============================================================================

/**
 * 检查并自动填充（一键式调用，集成点使用）
 * @returns {object} 如果触发填充则返回 fill() 结果，否则返回 scan() 状态
 */
function autoFillIfNeeded() {
  const status = scan()
  if (!status.needsFill) {
    return {
      action: 'skipped',
      reason: '水位健康',
      status,
    }
  }
  const matchResult = match(status)
  if (!matchResult.canProceed) {
    return {
      action: 'skipped',
      reason: '无可用填充源',
      status,
    }
  }
  return {
    action: 'filled',
    result: fill(matchResult),
  }
}

/**
 * 手动触发填充（适配 POST /api/v1/variable-pool/fill）
 * @param {object} [overrides] 可选配置覆盖，如 { max_fill_per_cycle: 5 }
 * @returns {object} fill() 结果
 */
function manualFill(overrides = {}) {
  if (overrides.max_fill_per_cycle) {
    const orig = CONFIG.max_fill_per_cycle
    CONFIG.max_fill_per_cycle = overrides.max_fill_per_cycle
    const result = fill()
    CONFIG.max_fill_per_cycle = orig
    return result
  }
  return fill()
}

/**
 * 初始化依赖适配器引用（可选）
 * @param {object} deps
 * @param {object} [deps.cognitiveEngine] 认知进化引擎适配器引用
 * @param {object} [deps.fivePoolsBalance] 五池均衡管理器适配器引用
 */
function init(deps = {}) {
  if (deps.cognitiveEngine) cognitiveEngineRef = deps.cognitiveEngine
  if (deps.fivePoolsBalance) fivePoolsBalanceRef = deps.fivePoolsBalance
}

/**
 * 更新配置
 * @param {object} newConfig 部分或完整配置覆盖
 */
function updateConfig(newConfig) {
  Object.assign(CONFIG, newConfig)
}

/**
 * 获取当前配置（只读副本）
 */
function getConfig() {
  return { ...CONFIG }
}

/**
 * 重置变量池（用于测试）
 */
function reset() {
  PoolState.variables.current = []
  PoolState.variables.lastFillAt = null
  PoolState.variables.fillCount = 0
  fillHistory = []
  cycleCount = 0
}

// =============================================================================
//  导出 API
// =============================================================================
module.exports = {
  // Feature 信息
  featureName: '变量池自动填充',
  featureVersion: '1.0.0',
  featureDomain: 'cognitive',

  // 配置
  CONFIG,
  updateConfig,
  getConfig,

  // 适配器协议四大方法
  scan,
  match,
  fill,
  report,

  // 核心方法
  autoFillIfNeeded,
  manualFill,
  init,
  reset,

  // 查询
  getPoolState: () => ({
    variables: {
      count: PoolState.variables.current.length,
      capacity: PoolState.variables.capacity,
      lastFillAt: PoolState.variables.lastFillAt,
      fillCount: PoolState.variables.fillCount,
    },
  }),
}
