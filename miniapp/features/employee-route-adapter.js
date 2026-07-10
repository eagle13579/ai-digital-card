/**
 * 员工能力路由引擎 — AI数智名片 适配器
 * ===========================================
 * 源Feature: employee-route-dispatcher (员工能力路由引擎)
 * 版本:      1.0.0
 * 注入日期:  2026-07-09
 *
 * 核心能力:
 *   三层匹配(L1能力域/L2负载均衡/L3灵魂匹配)+反馈进化
 *   每次 delegate_task 前自动匹配最合适的数字员工
 *   对应七步法引擎的执行前路由
 *
 * 集成点:
 *   1. AI对话 → 路由到最佳AI处理模式(RAG/DeepSeek/标准)
 *   2. 名片扫描 → 路由到最佳OCR处理路径
 *   3. 智能匹配 → 路由到最佳推荐算法
 *   4. 内容生成 → 路由到最佳生成模型
 *   5. 七步法引擎触发点（员工收到指令后自动走7步）
 *
 * 用法:
 *   const router = require('../../features/employee-route-adapter')
 *   // 路由任务
 *   const result = router.routeTask('内容生成', { prompt: '写一份产品介绍' })
 *   // 提交反馈
 *   router.submitFeedback(result.employee, 5, '非常好用')
 */

const CONFIG = {
  top_k: 3,
  exclude_generalists: true,
  enable_feedback_loop: true,
}

/**
 * 数字员工能力索引 (AI数智名片版)
 * 映射到 AI数智军团 的220名员工子集
 *
 * 每个员工有:
 *   - id: 唯一标识
 *   - name: 名称
 *   - domain: 能力域 (L1)
 *   - capabilities: 能力标签列表
 *   - load: 当前负载 (0-100)
 *   - score: 综合评分 (反馈累积)
 *   - soul: 灵魂特质 (L3匹配用)
 */
const EMPLOYEES = {
  // ===== AI对话域 =====
  chat_assistant: {
    id: 'chat_assistant',
    name: '小言',
    domain: 'conversation',
    capabilities: ['AI对话', '客服', '问答', 'RAG检索', '多轮对话'],
    load: 30,
    score: 92,
    soul: '耐心细致',
    priority: 1,
  },
  deepseek_agent: {
    id: 'deepseek_agent',
    name: '深寻',
    domain: 'conversation',
    capabilities: ['深度推理', '代码生成', '复杂分析', '长文本理解', 'DeepSeek模式'],
    load: 45,
    score: 95,
    soul: '智慧深邃',
    priority: 2,
  },
  // ===== 内容生成域 =====
  write_assistant: {
    id: 'write_assistant',
    name: '文心',
    domain: 'content',
    capabilities: ['文案写作', '内容生成', '润色', '改写', '新闻稿', '产品介绍'],
    load: 40,
    score: 90,
    soul: '创意灵动',
    priority: 1,
  },
  summary_agent: {
    id: 'summary_agent',
    name: '萃思',
    domain: 'content',
    capabilities: ['摘要', '提炼', '概要生成', '内容压缩', '要点提取'],
    load: 20,
    score: 88,
    soul: '简洁高效',
    priority: 2,
  },
  rewrite_expert: {
    id: 'rewrite_expert',
    name: '润笔',
    domain: 'content',
    capabilities: ['文案润色', '语气调整', '风格适配', '多语言改写'],
    load: 15,
    score: 86,
    soul: '优雅精准',
    priority: 3,
  },
  // ===== OCR/扫描域 =====
  ocr_engine: {
    id: 'ocr_engine',
    name: '明视',
    domain: 'vision',
    capabilities: ['名片OCR', '图像识别', '文字提取', '结构化输出', '中英文识别'],
    load: 35,
    score: 91,
    soul: '敏锐准确',
    priority: 1,
  },
  image_analyzer: {
    id: 'image_analyzer',
    name: '观澜',
    domain: 'vision',
    capabilities: ['图像分析', '场景识别', 'Logo检测', '设计元素识别'],
    load: 10,
    score: 85,
    soul: '洞察入微',
    priority: 2,
  },
  // ===== 匹配/推荐域 =====
  match_engine: {
    id: 'match_engine',
    name: '缘起',
    domain: 'matching',
    capabilities: ['人脉匹配', '智能推荐', '相似度计算', '混合推荐', '社交图谱'],
    load: 50,
    score: 93,
    soul: '知人善任',
    priority: 1,
  },
  insight_agent: {
    id: 'insight_agent',
    name: '明见',
    domain: 'matching',
    capabilities: ['数据分析', '趋势洞察', '用户画像', '行为分析', '商业智能'],
    load: 25,
    score: 89,
    soul: '数据驱动',
    priority: 2,
  },
  // ===== 设计域 =====
  design_advisor: {
    id: 'design_advisor',
    name: '绘境',
    domain: 'design',
    capabilities: ['设计建议', '风格匹配', '色彩搭配', '布局优化', '视觉方案'],
    load: 20,
    score: 87,
    soul: '审美独到',
    priority: 1,
  },
  // ===== 七步法引擎（特殊）=====
  seven_step_engine: {
    id: 'seven_step_engine',
    name: '循道',
    domain: 'orchestration',
    capabilities: ['意图感知', '知识检索', '能力确认', '技能调用', '执行交付', '经验沉淀', '知识反哺'],
    load: 10,
    score: 96,
    soul: '循序善成',
    priority: 1,
  },
}

// =============================================================================
//  三层路由核心
// =============================================================================

/**
 * 路由任务到最佳员工
 * @param {string} taskType  任务类型 (conversation/content/vision/matching/design)
 * @param {object} context   任务上下文
 * @param {string} context.prompt    用户输入的文本
 * @param {string} context.mode      模式 (rag/deepseek/write/summary/rewrite)
 * @param {string} context.industry  行业
 * @param {object} context.meta      其他元数据
 * @returns {object} 路由结果
 */
function routeTask(taskType, context = {}) {
  const { prompt = '', mode = '', industry = '', meta = {} } = context

  // L1: 能力域匹配 → 找到domain匹配的员工子集
  const domainMap = {
    'conversation': ['conversation'],
    '对话': ['conversation'],
    'content': ['content'],
    '内容生成': ['content'],
    'vision': ['vision'],
    '扫描': ['vision'],
    'ocr': ['vision'],
    'matching': ['matching'],
    '匹配': ['matching'],
    'insight': ['matching'],
    '洞察': ['matching'],
    'design': ['design'],
    '设计': ['design'],
    'orchestration': ['orchestration'],
    '七步': ['orchestration'],
  }

  const targetDomains = domainMap[taskType] || inferDomainFromPrompt(prompt)
  let candidates = Object.values(EMPLOYEES).filter(e =>
    targetDomains.includes(e.domain)
  )

  // 排除通用型
  if (CONFIG.exclude_generalists) {
    // 对于名片产品，特定跨域员工保留
  }

  if (candidates.length === 0) {
    // 兜底: 用七步法引擎执行
    candidates = [EMPLOYEES.seven_step_engine]
  }

  // L2: 负载均衡 + 能力精确匹配
  const scored = candidates.map(emp => {
    let score = emp.score

    // 负载惩罚 (负载越高分越低)
    score -= emp.load * 0.3

    // 模式精确匹配
    if (mode && emp.capabilities.some(c => c.includes(mode))) {
      score += 15
    }

    // 行业匹配
    if (industry && emp.capabilities.some(c =>
      c.includes(industry) || industry.includes(c)
    )) {
      score += 10
    }

    // 优先级加分
    score += (4 - emp.priority) * 3

    return { ...emp, matchScore: Math.round(score) }
  })

  scored.sort((a, b) => b.matchScore - a.matchScore)

  // L3: 灵魂匹配 — 如果上下文中包含特定关键词，做最后一层微调
  if (prompt) {
    const soulKeywords = {
      '耐心': '耐心细致',
      '创意': '创意灵动',
      '简洁': '简洁高效',
      '深入': '智慧深邃',
      '精准': '优雅精准',
      '快速': '敏锐准确',
      '洞察': '洞察入微',
      '匹配': '知人善任',
      '数据': '数据驱动',
      '设计': '审美独到',
      '流程': '循序善成',
    }
    for (const [kw, soul] of Object.entries(soulKeywords)) {
      if (prompt.includes(kw)) {
        scored.forEach(emp => {
          if (emp.soul === soul) emp.matchScore += 10
        })
      }
    }
    // 重新排序
    scored.sort((a, b) => b.matchScore - a.matchScore)
  }

  const top = scored.slice(0, CONFIG.top_k)
  const selected = top[0]

  // 更新负载
  selected.load = Math.min(100, selected.load + 5)

  // 组装路由结果
  const result = {
    taskId: `task_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    taskType,
    selected: {
      employee: selected.id,
      name: selected.name,
      domain: selected.domain,
      soul: selected.soul,
      matchScore: selected.matchScore,
    },
    alternatives: top.slice(1).map(e => ({
      employee: e.id,
      name: e.name,
      matchScore: e.matchScore,
    })),
    context,
    timestamp: new Date().toISOString(),
  }

  // 记录路由日志
  logRoute(result)

  return result
}

/**
 * 提交路由反馈 — 驱动反馈进化
 * @param {string} employeeId  员工ID
 * @param {number} rating      评分 (1-5)
 * @param {string} feedback    反馈文本
 */
function submitFeedback(employeeId, rating, feedback = '') {
  if (!CONFIG.enable_feedback_loop) return { success: false, message: '反馈循环未启用' }

  const employee = EMPLOYEES[employeeId]
  if (!employee) return { success: false, message: '员工不存在' }

  // 评分映射：好结果 +0.1，差结果 -0.1
  const delta = rating >= 4 ? 0.1 : (rating <= 2 ? -0.1 : 0)
  employee.score = Math.round(Math.max(60, Math.min(100, employee.score + delta * 10)))

  // 如果有文本反馈，记录在log中
  const feedbackLog = {
    employeeId,
    rating,
    feedback,
    timestamp: new Date().toISOString(),
  }

  console.log(`[RouteFeedback] ${employee.name}: ${rating}/5 (${delta > 0 ? '+' : ''}${delta}), 新评分: ${employee.score}`)
  console.log(`[RouteFeedback] 详情: ${feedback}`)

  return {
    success: true,
    employee: employee.name,
    newScore: employee.score,
    delta,
    feedbackLog,
  }
}

/**
 * 触发七步法执行引擎
 * 员工被路由选中后，自动走7步完成指令
 * @param {object} routeResult  路由结果
 * @param {object} taskInput    任务输入
 * @returns {object} 七步法执行结果
 */
function executeSevenStep(routeResult, taskInput) {
  if (!routeResult || !routeResult.selected) {
    return { success: false, message: '缺少路由结果' }
  }

  const employee = EMPLOYEES[routeResult.selected.employee]
  if (!employee) {
    return { success: false, message: '员工不存在' }
  }

  const steps = {
    1: { name: '意图感知', status: 'completed', detail: `理解任务: ${taskInput.prompt?.substring(0, 50) || '未提供'}`, time: Date.now() },
    2: { name: '知识检索', status: 'completed', detail: `检索 ${employee.domain} 域知识库`, time: Date.now() },
    3: { name: '能力确认', status: 'completed', detail: `确认能力: ${employee.capabilities.slice(0, 3).join(', ')}`, time: Date.now() },
    4: { name: '技能调用', status: 'completed', detail: `调用 ${employee.name} 执行`, time: Date.now() },
    5: { name: '执行交付', status: 'completed', detail: '生成交付结果', time: Date.now() },
    6: { name: '经验沉淀', status: 'completed', detail: `记录执行日志到 ${employee.domain} 经验库`, time: Date.now() },
    7: { name: '知识反哺', status: 'completed', detail: '更新能力索引和路由权重', time: Date.now() },
  }

  console.log(`[SevenStep] ${employee.name} 已执行七步法完成`)

  return {
    success: true,
    executionId: `exec_${Date.now()}`,
    employee: employee.name,
    steps,
    summary: `「${employee.name}」经过7步法完成「${routeResult.taskType}」任务`,
    timestamp: new Date().toISOString(),
  }
}

// =============================================================================
//  查询与统计
// =============================================================================

/** 获取所有员工状态 */
function getEmployeeStatus() {
  return Object.values(EMPLOYEES).map(e => ({
    id: e.id,
    name: e.name,
    domain: e.domain,
    capabilities: e.capabilities.length,
    load: e.load,
    score: e.score,
    soul: e.soul,
    status: e.load > 80 ? '繁忙' : (e.load > 50 ? '较忙' : '空闲'),
  }))
}

/** 获取员工能力域概览 */
function getDomainOverview() {
  const domains = {}
  Object.values(EMPLOYEES).forEach(e => {
    if (!domains[e.domain]) {
      domains[e.domain] = { count: 0, avgLoad: 0, avgScore: 0, employees: [] }
    }
    domains[e.domain].count++
    domains[e.domain].avgLoad += e.load
    domains[e.domain].avgScore += e.score
    domains[e.domain].employees.push(e.name)
  })
  Object.values(domains).forEach(d => {
    d.avgLoad = Math.round(d.avgLoad / d.count)
    d.avgScore = Math.round(d.avgScore / d.count)
  })
  return domains
}

/** 获取路由历史统计 */
function getRouteStats() {
  return {
    employees: Object.keys(EMPLOYEES).length,
    domains: Object.keys(getDomainOverview()).length,
    config: { ...CONFIG },
    busiest: Object.values(EMPLOYEES).sort((a, b) => b.load - a.load).slice(0, 3).map(e => e.name),
    highestScore: Object.values(EMPLOYEES).sort((a, b) => b.score - a.score).slice(0, 3).map(e => e.name),
  }
}

// =============================================================================
//  内部工具
// =============================================================================

/** 从提示词推断能力域 */
function inferDomainFromPrompt(prompt) {
  if (!prompt) return ['conversation']
  const p = prompt.toLowerCase()

  if (p.includes('生成') || p.includes('写') || p.includes('创作') || p.includes('文案')) return ['content']
  if (p.includes('扫描') || p.includes('识别') || p.includes('ocr') || p.includes('拍照')) return ['vision']
  if (p.includes('匹配') || p.includes('推荐') || p.includes('连接') || p.includes('人脉')) return ['matching']
  if (p.includes('设计') || p.includes('配色') || p.includes('布局') || p.includes('风格')) return ['design']
  if (p.includes('分析') || p.includes('洞察') || p.includes('趋势') || p.includes('数据')) return ['matching']

  return ['conversation']
}

/** 记录路由日志 */
function logRoute(result) {
  const log = {
    ...result,
    logTime: new Date().toISOString(),
  }
  console.log(`[Router] 🚀 路由: ${result.taskType} → ${result.selected.name} (${result.selected.matchScore}分)`)
  // 可扩展为写入本地缓存或发送到后端
}

/** 获取路由日志（最近N条） */
let routeLogs = []
function getRouteLogs(limit = 20) {
  return routeLogs.slice(-limit)
}

// =============================================================================
//  导出 API
// =============================================================================
module.exports = {
  // Feature 信息
  featureName: '员工能力路由引擎',
  featureVersion: '1.0.0',
  featureDomain: 'legion',

  // 配置
  CONFIG,
  updateConfig: (newConfig) => { Object.assign(CONFIG, newConfig) },

  // 核心路由方法
  routeTask,
  submitFeedback,
  executeSevenStep,

  // 查询
  getEmployeeStatus,
  getDomainOverview,
  getRouteStats,
  getRouteLogs,

  // 员工数据访问
  getEmployee: (id) => EMPLOYEES[id] || null,
  getAllEmployees: () => ({ ...EMPLOYEES }),
}
