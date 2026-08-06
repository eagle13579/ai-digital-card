/**
 * 认知进化引擎 — AI数智名片 适配器
 * ===========================================
 * 源Feature: cognitive-evolution-engine (认知进化引擎)
 * 版本:      1.0.0
 * 注入日期:  2026-07-09
 *
 * 核心能力:
 *   6步拆解法 + 五池循环（现象池/变量池/模型池/决策验证池/行动池）
 *   任何输入自动拆解为认知资产
 *
 * 集成点:
 *   1. AI对话 → 自动萃取认知资产（包装 aiApi.getChat）
 *   2. AI内容生成 → 认知模型产出（包装 aiApi.generate）
 *   3. AI名片扫描 → 现象池输入（包装 scan/index.js 的 OCR结果）
 *   4. AI数据洞察 → 模型池 + 决策验证池（包装 insight/index.js）
 *   5. 智能人脉匹配 → 行动池输出
 *
 * 用法:
 *   const cognitiveAdapter = require('../../features/cognitive-evolution-adapter')
 *   // 自动萃取
 *   cognitiveAdapter.extractFromChat(message, response)
 *   // 查询五池状态
 *   cognitiveAdapter.getPoolsStatus()
 */

const CONFIG = {
  auto_extract: true,
  pool_sync_interval: 60,  // 分钟
  max_models_per_session: 5,
}

/**
 * 五池数据结构（本地缓存 + 可选远程同步）
 */
const Pools = {
  /** 现象池 — 原始输入/观察/数据点 */
  phenomena: [],
  /** 变量池 — 从现象中提取的关键变量/维度 */
  variables: [],
  /** 模型池 — 心智模型/模式/理论 */
  models: [],
  /** 决策验证池 — 已验证/待验证的决策假设 */
  decisions: [],
  /** 行动池 — 可执行的行动/建议 */
  actions: [],
}

// =============================================================================
//  核心认知萃取管道
// =============================================================================

/**
 * 从AI对话中自动萃取认知资产
 * @param {string} message   用户原始消息
 * @param {string|object} response  AI回复内容
 * @returns {{ phenomena: number, variables: number, models: number, decisions: number, actions: number }}
 */
function extractFromChat(message, response) {
  if (!CONFIG.auto_extract) return getPoolCounts()

  const responseText = typeof response === 'object' ? (response.content || JSON.stringify(response)) : response

  // 1. 现象池 — 存入用户输入
  Pools.phenomena.push({
    id: `phen_${Date.now()}`,
    source: 'chat',
    content: message.substring(0, 500),
    timestamp: new Date().toISOString(),
    tags: extractTags(message),
  })

  // 2. 变量池 — 从AI回复中提取关键变量
  const extractedVars = extractVariables(responseText)
  extractedVars.forEach(v => {
    Pools.variables.push({
      id: `var_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name: v.name,
      value: v.value,
      confidence: v.confidence || 0.7,
      source: 'chat_analysis',
      timestamp: new Date().toISOString(),
    })
  })

  // 3. 模型池 — 检测到模式/规律时创建心智模型
  const extractedModels = extractModels(responseText)
  if (extractedModels.length > 0 && getPoolCounts().models < CONFIG.max_models_per_session) {
    extractedModels.forEach(m => {
      Pools.models.push({
        id: `model_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        name: m.name,
        description: m.description,
        evidence: m.evidence,
        timestamp: new Date().toISOString(),
      })
    })
  }

  // 4. 决策验证池 — 检测建议/决策
  const extractedDecisions = extractDecisions(responseText)
  extractedDecisions.forEach(d => {
    Pools.decisions.push({
      id: `dec_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      hypothesis: d.hypothesis,
      status: 'pending',  // pending | verified | rejected
      evidence: d.evidence || '',
      timestamp: new Date().toISOString(),
    })
  })

  // 5. 行动池 — 检测可执行行动
  const extractedActions = extractActions(responseText)
  extractedActions.forEach(a => {
    Pools.actions.push({
      id: `act_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      description: a.description,
      priority: a.priority || 'medium',
      status: 'pending',  // pending | done | archived
      timestamp: new Date().toISOString(),
    })
  })

  trimPools()
  return getPoolCounts()
}

/**
 * 从名片扫描结果中萃取认知资产
 * @param {object} scanResult  名片扫描结果（含 name, title, company 等）
 */
function extractFromScan(scanResult) {
  if (!scanResult) return getPoolCounts()

  // 现象池：存入扫描原始数据
  Pools.phenomena.push({
    id: `phen_${Date.now()}`,
    source: 'scan',
    content: JSON.stringify(scanResult),
    type: 'business_card',
    timestamp: new Date().toISOString(),
    tags: [scanResult.company, scanResult.title, scanResult.name].filter(Boolean),
  })

  // 变量池：姓名/职位/公司/联系方式
  if (scanResult.name) {
    Pools.variables.push({
      id: `var_${Date.now()}_name`,
      name: '联系人',
      value: scanResult.name,
      confidence: 0.95,
      source: 'ocr',
      timestamp: new Date().toISOString(),
    })
  }
  if (scanResult.company) {
    Pools.variables.push({
      id: `var_${Date.now()}_company`,
      name: '公司',
      value: scanResult.company,
      confidence: 0.9,
      source: 'ocr',
      timestamp: new Date().toISOString(),
    })
  }
  if (scanResult.title) {
    Pools.variables.push({
      id: `var_${Date.now()}_title`,
      name: '职位',
      value: scanResult.title,
      confidence: 0.85,
      source: 'ocr',
      timestamp: new Date().toISOString(),
    })
  }

  // 行动池：创建联系/发送名片/跟进
  Pools.actions.push({
    id: `act_${Date.now()}_followup`,
    description: `跟进 ${scanResult.name || '该联系人'} — 发送名片或邀约`,
    priority: 'high',
    status: 'pending',
    timestamp: new Date().toISOString(),
  })

  trimPools()
  return getPoolCounts()
}

/**
 * 从人脉匹配结果中萃取认知资产
 * @param {object} matchResult  匹配推荐数据
 */
function extractFromMatch(matchResult) {
  if (!matchResult) return getPoolCounts()

  Pools.phenomena.push({
    id: `phen_${Date.now()}`,
    source: 'match',
    content: JSON.stringify(matchResult),
    type: 'network_match',
    timestamp: new Date().toISOString(),
  })

  // 行动池
  Pools.actions.push({
    id: `act_${Date.now()}_connect`,
    description: `与 ${matchResult.name || '匹配对象'} 建立连接`,
    priority: 'medium',
    status: 'pending',
    timestamp: new Date().toISOString(),
  })

  trimPools()
  return getPoolCounts()
}

// =============================================================================
//  查询与同步
// =============================================================================

/** 获取五池当前数量 */
function getPoolCounts() {
  return {
    phenomena: Pools.phenomena.length,
    variables: Pools.variables.length,
    models: Pools.models.length,
    decisions: Pools.decisions.length,
    actions: Pools.actions.length,
  }
}

/** 获取五池详细状态 */
function getPoolsStatus() {
  return {
    counts: getPoolCounts(),
    lastSync: new Date().toISOString(),
    config: { ...CONFIG },
    pools: {
      phenomena: Pools.phenomena.slice(-10),
      variables: Pools.variables.slice(-10),
      models: Pools.models.slice(-10),
      decisions: Pools.decisions.slice(-10),
      actions: Pools.actions.slice(-10),
    },
  }
}

/** 手动触发认知萃取（适配 /api/v1/cognitive/extract） */
function manualExtract(input, source = 'manual') {
  Pools.phenomena.push({
    id: `phen_${Date.now()}`,
    source,
    content: typeof input === 'string' ? input : JSON.stringify(input),
    timestamp: new Date().toISOString(),
  })
  trimPools()
  return getPoolCounts()
}

/** 清理超出上限的池数据（仅保留最新200条/池） */
function trimPools() {
  const MAX_PER_POOL = 200
  for (const key of Object.keys(Pools)) {
    if (Pools[key].length > MAX_PER_POOL) {
      Pools[key] = Pools[key].slice(-MAX_PER_POOL)
    }
  }
}

// =============================================================================
//  辅助函数
// =============================================================================

/** 简单标签提取 */
function extractTags(text) {
  const tags = []
  // 匹配 #标签 格式
  const hashtagMatches = text.match(/#([\u4e00-\u9fa5\w]+)/g)
  if (hashtagMatches) {
    hashtagMatches.forEach(t => tags.push(t.replace('#', '')))
  }
  return tags
}

/** 从文本中提取变量 */
function extractVariables(text) {
  const vars = []
  // 匹配 "xxx 是 yyy" / "xxx: yyy" 这类结构化表达
  const pattern = /(['"」]?)([\u4e00-\u9fa5\w\s]{2,30}?)\1[:：是](.+?)(?=[。，；\n]|$)/g
  let match
  while ((match = pattern.exec(text)) !== null) {
    const name = match[2].trim()
    const value = match[3].trim()
    if (name && value && name.length > 1 && value.length > 1) {
      vars.push({ name, value, confidence: 0.6 })
    }
  }
  return vars.slice(0, 5)
}

/** 从文本中提取心智模型 */
function extractModels(text) {
  const models = []
  // 匹配 "模式/规律/原理: " 引导的句子
  const modelPatterns = [
    /(模式|规律|原理|法则|效应|理论)[：:]\s*(.+?)(?=[。\n]|$)/g,
    /(核心|关键|本质)[：:]\s*(.+?)(?=[。\n]|$)/g,
  ]
  modelPatterns.forEach(re => {
    let m
    while ((m = re.exec(text)) !== null) {
      models.push({
        name: m[1],
        description: m[2].trim(),
        evidence: text.substring(0, 100),
      })
    }
  })
  return models.slice(0, 3)
}

/** 从文本中提取决策假设 */
function extractDecisions(text) {
  const decisions = []
  const patterns = [
    /建议[(（]?(\d+)[)）]?[：:]\s*(.+?)(?=[。\n]|$)/g,
    /(建议|推荐|可以考虑)[：:]\s*(.+?)(?=[。\n]|$)/g,
  ]
  patterns.forEach(re => {
    let m
    while ((m = re.exec(text)) !== null) {
      decisions.push({
        hypothesis: m[2] || m[1],
        evidence: '来自AI分析',
      })
    }
  })
  return decisions.slice(0, 3)
}

/** 从文本中提取行动项 */
function extractActions(text) {
  const actions = []
  const patterns = [
    /下一步[：:]\s*(.+?)(?=[。\n]|$)/g,
    /(请|可以|需要)(尝试|联系|发送|创建|设置|查看)(.+?)(?=[。\n]|$)/g,
  ]
  patterns.forEach(re => {
    let m
    while ((m = re.exec(text)) !== null) {
      actions.push({
        description: m[0].trim(),
        priority: 'medium',
      })
    }
  })
  return actions.slice(0, 3)
}

// =============================================================================
//  导出 API
// =============================================================================
module.exports = {
  // Feature 信息
  featureName: '认知进化引擎',
  featureVersion: '1.0.0',
  featureDomain: 'cognitive',

  // 配置
  CONFIG,
  updateConfig: (newConfig) => {
    Object.assign(CONFIG, newConfig)
  },

  // 核心萃取方法
  extractFromChat,
  extractFromScan,
  extractFromMatch,
  manualExtract,

  // 查询
  getPoolCounts,
  getPoolsStatus,

  // 池数据访问（仅供高级使用）
  getPools: () => ({ ...Pools }),
}
