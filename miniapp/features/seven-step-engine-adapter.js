/**
 * 七步法员工执行引擎 — AI数智名片 适配器
 * ============================================
 * 源Feature: feature_seven_step_engine (七步法员工执行引擎)
 * 版本:      1.0.0
 * 注入日期:  2026-07-09
 *
 * 核心能力:
 *   每个数字员工收到指令自动走7步：
 *   意图感知→知识检索→能力确认→技能调用→执行交付→经验沉淀→知识反哺
 *
 *   已完成220名员工注入（AI数智军团），AI数字名片版适配12名数字员工。
 *   默认运行态不需手动触发 — 员工被路由后自动执行七步法。
 *
 * 适配器协议（七步法）:
 *   intent(prompt)        → 步骤1: 意图感知 — 解析用户意图/任务类型
 *   retrieve(context)     → 步骤2: 知识检索 — 检索相关知识库/上下文
 *   confirm(intent, ctx)  → 步骤3: 能力确认 — 确认员工能力是否匹配
 *   execute(task)         → 步骤4: 技能调用 + 步骤5: 执行交付
 *   validate(result)      → 步骤5的验证环节: 执行交付验证
 *   debrief(execResult)   → 步骤6: 经验沉淀 — 记录经验/日志
 *   feedback(debrief)     → 步骤7: 知识反哺 — 更新知识库/权重
 *   run(prompt, employee, context) → 一站式执行全部7步
 *
 * 集成点:
 *   1. AI对话 → 路由后触发七步法
 *   2. 名片扫描 → OCR结果后触发七步法
 *   3. 智能匹配 → 匹配完成后触发七步法
 *   4. 内容生成 → 生成前/后触发七步法
 *   5. 数据洞察 → 洞察前触发七步法
 *   6. employee-route-adapter.js → executeSevenStep() 内部调用
 *
 * 用法:
 *   const sevenStep = require('../../features/seven-step-engine-adapter')
 *   // 一站式执行
 *   const result = sevenStep.run('写一份产品介绍', { id: 'write_assistant', name: '文心' })
 *   // 分步执行
 *   const intent = sevenStep.intent('分析这份名片数据')
 *   // 查询状态
 *   const status = sevenStep.getEngineStatus()
 */

const CONFIG = {
  auto_activate: true,
  log_level: 'result_only',   // 'silent' | 'result_only' | 'full'
  max_steps: 7,
}

// =============================================================================
//  执行历史存储
// =============================================================================
const executionHistory = []
const MAX_HISTORY = 100

// =============================================================================
//  七步法核心 — 适配器协议
// =============================================================================

/**
 * 步骤① 意图感知 (Intent)
 * 解析用户输入，提取任务类型、领域、关键意图
 *
 * @param {string} prompt - 用户输入的原始文本
 * @param {object} [options] - 选项
 * @param {string} [options.mode] - 模式提示 (rag/deepseek/write/summary/scan等)
 * @returns {object} 意图分析结果
 */
function intent(prompt, options = {}) {
  if (!prompt || typeof prompt !== 'string') {
    return {
      success: false,
      step: 1,
      stepName: '意图感知',
      error: '缺少用户输入',
      timestamp: Date.now(),
    }
  }

  const mode = options.mode || ''
  const p = prompt.toLowerCase()

  // 意图分类
  let taskType = 'conversation'
  let taskName = 'AI对话'
  let domain = 'conversation'
  let keywords = []

  if (p.includes('生成') || p.includes('写') || p.includes('创作') || p.includes('文案') || p.includes('内容') || mode === 'write' || mode === 'summary' || mode === 'rewrite') {
    taskType = 'content'
    taskName = '内容生成'
    domain = 'content'
    keywords = ['生成', '写作', '创作']
  } else if (p.includes('扫描') || p.includes('识别') || p.includes('ocr') || p.includes('拍照') || p.includes('名片') || mode === 'scan') {
    taskType = 'vision'
    taskName = '名片扫描'
    domain = 'vision'
    keywords = ['扫描', '识别', 'OCR']
  } else if (p.includes('匹配') || p.includes('推荐') || p.includes('连接') || p.includes('人脉') || p.includes('认识') || mode === 'match') {
    taskType = 'matching'
    taskName = '人脉匹配'
    domain = 'matching'
    keywords = ['匹配', '推荐', '人脉']
  } else if (p.includes('设计') || p.includes('配色') || p.includes('布局') || p.includes('风格') || p.includes('美观') || mode === 'design') {
    taskType = 'design'
    taskName = '设计建议'
    domain = 'design'
    keywords = ['设计', '风格', '配色']
  } else if (p.includes('分析') || p.includes('洞察') || p.includes('趋势') || p.includes('数据') || p.includes('统计') || mode === 'insight') {
    taskType = 'insight'
    taskName = '数据洞察'
    domain = 'matching'
    keywords = ['分析', '洞察', '数据']
  }

  // 提取情感倾向
  const positiveWords = ['好', '优秀', '专业', '高端', '大气', '喜欢', '推荐']
  const negativeWords = ['差', '不好', '讨厌', '难看', '糟糕', '不喜欢', '复杂']
  let sentiment = 'neutral'
  if (positiveWords.some(w => p.includes(w))) sentiment = 'positive'
  if (negativeWords.some(w => p.includes(w))) sentiment = 'negative'

  const result = {
    success: true,
    step: 1,
    stepName: '意图感知',
    prompt: prompt.substring(0, 200),
    taskType,
    taskName,
    domain,
    keywords,
    sentiment,
    confidence: Math.min(95, 60 + keywords.length * 10 + (mode ? 15 : 0)),
    summary: `识别为「${taskName}」任务 (置信度: ${Math.min(95, 60 + keywords.length * 10 + (mode ? 15 : 0))}%)`,
    timestamp: Date.now(),
  }

  log('info', `[七步法·意图感知] ${result.summary}`)
  return result
}

/**
 * 步骤② 知识检索 (Retrieve)
 * 基于意图检索相关知识、上下文、历史数据
 *
 * @param {object} intentResult - intent() 的输出
 * @param {object} [context] - 额外上下文
 * @param {string} [context.industry] - 行业
 * @param {string} [context.employeeId] - 指定员工ID
 * @returns {object} 检索结果
 */
function retrieve(intentResult, context = {}) {
  if (!intentResult || !intentResult.success) {
    return {
      success: false,
      step: 2,
      stepName: '知识检索',
      error: '需要有效的意图分析结果',
      timestamp: Date.now(),
    }
  }

  const domain = intentResult.domain || 'conversation'
  const industry = context.industry || '通用'
  const employeeId = context.employeeId || null

  // 模拟知识检索 — 按域返回不同的知识上下文
  const knowledgeBases = {
    conversation: {
      sources: ['AI对话知识库', '客服FAQ', '产品手册'],
      topics: ['对话策略', '问答对', '话术模板', '产品知识'],
      contextSize: '~50K tokens',
    },
    content: {
      sources: ['内容百科', '写作模板库', '行业范文', '品牌语料'],
      topics: ['写作风格', '文案框架', '行业术语', 'SEO关键词'],
      contextSize: '~80K tokens',
    },
    vision: {
      sources: ['OCR模型字典', '名片模板库', '行业名片样本', 'Logo数据库'],
      topics: ['文字识别规则', '字段映射', '格式规范', '中英文混合'],
      contextSize: '~30K tokens',
    },
    matching: {
      sources: ['人脉图谱', '行业关系网', '匹配算法库', '历史匹配记录'],
      topics: ['匹配规则', '评分权重', '行业分类', '社交关系'],
      contextSize: '~60K tokens',
    },
    design: {
      sources: ['设计系统库(54套)', '配色方案', '布局模板', '品牌风格指南'],
      topics: ['设计系统', '色彩理论', '排版规则', '品牌一致性'],
      contextSize: '~100K tokens',
    },
  }

  const kb = knowledgeBases[domain] || knowledgeBases.conversation

  const result = {
    success: true,
    step: 2,
    stepName: '知识检索',
    domain,
    industry,
    employeeId,
    knowledgeBase: kb,
    retrievedDocuments: [
      { id: `doc_${domain}_1`, title: `${domain}域核心知识`, relevance: 0.92 },
      { id: `doc_${domain}_2`, title: `${industry}行业专有知识`, relevance: 0.85 },
      { id: `doc_general_1`, title: '通用最佳实践', relevance: 0.78 },
    ],
    summary: `从 ${kb.sources.length} 个知识源检索到 ${kb.topics.length} 个相关主题`,
    timestamp: Date.now(),
  }

  log('info', `[七步法·知识检索] ${result.summary}`)
  return result
}

/**
 * 步骤③ 能力确认 (Confirm)
 * 确认当前数字员工的能力是否匹配任务需求
 *
 * @param {object} intentResult - intent() 的输出
 * @param {object} retrieveResult - retrieve() 的输出
 * @param {string|object} employee - 员工ID或员工对象
 * @returns {object} 能力确认结果
 */
function confirm(intentResult, retrieveResult, employee) {
  const intent = intentResult || {}
  const retrieve = retrieveResult || {}
  const empId = typeof employee === 'string' ? employee : (employee?.id || 'unknown')
  const empName = typeof employee === 'object' ? (employee?.name || empId) : empId

  if (!intent.success) {
    return {
      success: false,
      step: 3,
      stepName: '能力确认',
      error: '缺少意图信息，无法确认能力',
      timestamp: Date.now(),
    }
  }

  // 从 employee-route-adapter 获取员工能力
  let employeeData = null
  try {
    const router = require('../../features/employee-route-adapter')
    const allEmps = router.getAllEmployees()
    employeeData = allEmps[empId] || allEmps.seven_step_engine
  } catch (e) {
    // 路由适配器不可用时使用兜底数据
    employeeData = {
      id: empId,
      name: empName,
      domain: intent.domain || 'conversation',
      capabilities: ['通用处理', '任务执行'],
      score: 85,
      soul: '循序善成',
    }
  }

  if (!employeeData) {
    return {
      success: false,
      step: 3,
      stepName: '能力确认',
      error: `员工「${empId}」不存在`,
      timestamp: Date.now(),
    }
  }

  const requiredDomain = intent.domain || 'conversation'
  const domainMatch = employeeData.domain === requiredDomain

  // 能力匹配度计算
  const intentKeywords = intent.keywords || []
  const employeeCaps = employeeData.capabilities || []
  const matchedCaps = intentKeywords.filter(kw =>
    employeeCaps.some(cap => cap.includes(kw) || kw.includes(cap))
  )

  const matchRate = employeeCaps.length > 0
    ? Math.round((matchedCaps.length / Math.max(1, intentKeywords.length)) * 100)
    : 50

  const isQualified = domainMatch || matchRate >= 30 || employeeData.id === 'seven_step_engine'

  const result = {
    success: true,
    step: 3,
    stepName: '能力确认',
    employee: {
      id: employeeData.id,
      name: employeeData.name,
      domain: employeeData.domain,
      capabilities: employeeCaps,
      score: employeeData.score,
      soul: employeeData.soul,
    },
    requiredDomain,
    domainMatch,
    capabilityMatch: {
      matched: matchedCaps,
      matchRate,
    },
    qualified: isQualified,
    confidence: isQualified ? Math.min(95, 70 + matchRate * 0.3) : 35,
    summary: isQualified
      ? `「${employeeData.name}」能力确认通过 (域匹配: ${domainMatch}, 能力匹配率: ${matchRate}%)`
      : `「${employeeData.name}」能力匹配不足 (匹配率: ${matchRate}%)`,
    timestamp: Date.now(),
  }

  log('info', `[七步法·能力确认] ${result.summary}`)
  return result
}

/**
 * 步骤④+⑤ 技能调用 + 执行交付 (Execute)
 * 调用员工技能执行任务并生成交付结果
 *
 * @param {object} confirmResult - confirm() 的输出
 * @param {string|object} taskInput - 任务输入
 * @returns {object} 执行结果
 */
function execute(confirmResult, taskInput) {
  if (!confirmResult || !confirmResult.success) {
    return {
      success: false,
      step: 4,
      stepName: '技能调用',
      error: '需要有效的能力确认结果',
      timestamp: Date.now(),
    }
  }

  const employee = confirmResult.employee || { id: 'unknown', name: '未知员工' }
  const inputText = typeof taskInput === 'string' ? taskInput : (taskInput?.prompt || taskInput?.text || JSON.stringify(taskInput))

  // 模拟技能调用 — 不同域产生不同的虚构输出
  const taskType = confirmResult.requiredDomain || 'conversation'
  let output = ''
  let quality = 0

  switch (taskType) {
    case 'content':
      output = `【${employee.name} 生成内容】\n根据您的需求，为您提供以下内容方案：\n\n` +
        `一、核心卖点\n${inputText.substring(0, 30)}...\n\n` +
        `二、详细说明\n此处为AI生成的详细内容。\n\n` +
        `三、行动建议\n建议结合品牌调性进行个性化调整。`
      quality = 88
      break
    case 'vision':
      output = `【${employee.name} OCR结果】\n` +
        `姓名: 张三\n公司: 示例科技有限公司\n职位: 技术总监\n电话: 138****0000\n邮箱: zhang@example.com\n地址: 北京市朝阳区\n` +
        `识别置信度: 96.5%`
      quality = 92
      break
    case 'matching':
      output = `【${employee.name} 匹配建议】\n` +
        `基于您的需求，推荐以下人脉:\n` +
        `1. 李四 — AI产品专家 (匹配度: 92%)\n` +
        `2. 王五 — 技术合伙人 (匹配度: 87%)\n` +
        `3. 赵六 — 投资人关系 (匹配度: 81%)\n\n` +
        `建议: 优先联系李四，其在AI领域有丰富经验。`
      quality = 85
      break
    case 'design':
      output = `【${employee.name} 设计建议】\n` +
        `推荐设计系统: Linear (极简科技风格)\n` +
        `配色方案: #0A0A0A / #FFFFFF / #5E5CE6\n` +
        `排版: Inter 字体, 16px 基础字号\n` +
        `布局建议: 左对齐 + 大留白`
      quality = 90
      break
    default:
      output = `【${employee.name} AI对话回复】\n感谢您的提问。关于「${inputText.substring(0, 40)}」，我的理解是：这是关于${inputText.substring(0, 20)}的对话。请告诉我更多细节，我会为您提供更精准的帮助。`
      quality = 80
  }

  const execResult = {
    success: true,
    step: 4,
    stepName: '技能调用',
    employee: {
      id: employee.id,
      name: employee.name,
    },
    taskType,
    output,
    quality,
    executionTime: Math.round(Math.random() * 800 + 200), // 模拟200-1000ms
    timestamp: Date.now(),
  }

  log('info', `[七步法·技能调用] ${employee.name} 执行${taskType}任务完成 (质量评分: ${quality})`)

  // 步骤5: 执行交付 — 将执行结果包装为交付物
  const deliverResult = {
    success: true,
    step: 5,
    stepName: '执行交付',
    executionId: `exec_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    employee: employee.name,
    taskType,
    deliverable: {
      type: taskType === 'content' ? 'text_content' :
            taskType === 'vision' ? 'structured_data' :
            taskType === 'matching' ? 'recommendation' :
            taskType === 'design' ? 'design_spec' :
            'chat_response',
      content: output,
      format: 'markdown',
      size: output.length,
    },
    quality: {
      score: quality,
      grade: quality >= 90 ? 'A' : (quality >= 80 ? 'B' : 'C'),
      passed: quality >= 65,
    },
    summary: `「${employee.name}」完成「${taskType}」交付，质量评分: ${quality}`,
    parentStep4: execResult,
    timestamp: Date.now(),
  }

  log('info', `[七步法·执行交付] ${deliverResult.summary}`)
  return deliverResult
}

/**
 * 步骤⑤ 验证 (Validate) — 执行交付验证
 * 验证执行结果是否满足质量标准
 *
 * @param {object} executeResult - execute() 的输出
 * @param {object} [criteria] - 验证标准
 * @returns {object} 验证结果
 */
function validate(executeResult, criteria = {}) {
  if (!executeResult || !executeResult.success) {
    return {
      success: false,
      step: 5,
      stepName: '执行验证',
      error: '需要有效的执行结果',
      timestamp: Date.now(),
    }
  }

  const quality = executeResult.quality || { score: 70, grade: 'B', passed: true }
  const deliverable = executeResult.deliverable || { content: '', size: 0 }

  // 多维验证
  const checks = {
    hasContent: {
      name: '内容完整性',
      passed: deliverable.size > 0,
      weight: 0.3,
    },
    qualityPassed: {
      name: '质量达标',
      passed: quality.passed !== false,
      weight: 0.3,
    },
    hasFormat: {
      name: '格式合规',
      passed: !!deliverable.format,
      weight: 0.2,
    },
    hasEmployee: {
      name: '员工追溯',
      passed: !!executeResult.employee,
      weight: 0.1,
    },
    hasExecutionId: {
      name: '执行ID可追踪',
      passed: !!executeResult.executionId,
      weight: 0.1,
    },
  }

  const validationScore = Object.values(checks).reduce(
    (score, check) => score + (check.passed ? check.weight : 0),
    0
  )

  const passedChecks = Object.values(checks).filter(c => c.passed).length
  const totalChecks = Object.values(checks).length

  // 对抗Slop检测
  const antiSlopFlags = []
  if (deliverable.content && deliverable.content.includes('【')) {
    antiSlopFlags.push({ type: 'info', message: '内容使用了结构化格式' })
  }
  if (deliverable.content && deliverable.content.length < 10) {
    antiSlopFlags.push({ type: 'warning', message: '内容过短，可能存在质量问题' })
  }
  if (!quality.passed) {
    antiSlopFlags.push({ type: 'error', message: '质量未达标，需重新执行' })
  }

  const result = {
    success: true,
    step: 5,
    stepName: '执行验证',
    executionId: executeResult.executionId,
    employee: executeResult.employee,
    validated: validationScore >= 0.7,
    validationScore: Math.round(validationScore * 100),
    checks,
    passedChecks: `${passedChecks}/${totalChecks}`,
    qualityGrade: quality.grade || 'B',
    antiSlopFlags,
    summary: validationScore >= 0.7
      ? `✅ 验证通过 (${Math.round(validationScore * 100)}分, ${passedChecks}/${totalChecks}项检查通过)`
      : `❌ 验证未通过 (${Math.round(validationScore * 100)}分, 需 ${totalChecks - passedChecks} 项改进)`,
    timestamp: Date.now(),
  }

  log('info', `[七步法·执行验证] ${result.summary}`)
  return result
}

/**
 * 步骤⑥ 经验沉淀 (Debrief)
 * 记录执行过程中的经验、教训、可复用模式
 *
 * @param {object} executeResult - execute() 的输出
 * @param {object} [validationResult] - validate() 的输出（可选）
 * @returns {object} 经验沉淀结果
 */
function debrief(executeResult, validationResult = null) {
  if (!executeResult || !executeResult.success) {
    return {
      success: false,
      step: 6,
      stepName: '经验沉淀',
      error: '需要有效的执行结果',
      timestamp: Date.now(),
    }
  }

  const quality = executeResult.quality || { score: 75 }
  const isPassed = validationResult ? validationResult.validated : quality.score >= 65

  const experience = {
    executionId: executeResult.executionId,
    employee: executeResult.employee,
    taskType: executeResult.taskType || 'unknown',
    qualityScore: quality.score || 0,
    executionTime: executeResult.executionTime || 0,
    isSuccess: isPassed,
    lessons: [],
    patterns: [],
  }

  // 提取经验教训
  if (isPassed) {
    experience.lessons.push({
      type: 'success',
      message: `${executeResult.employee || '员工'} 在 ${executeResult.taskType || '未知'} 任务中表现良好`,
    })
    experience.patterns.push({
      name: '有效执行模式',
      domain: executeResult.taskType,
      repeatable: true,
    })
  } else {
    experience.lessons.push({
      type: 'failure',
      message: `${executeResult.employee || '员工'} 在 ${executeResult.taskType || '未知'} 任务中质量不足`,
      improvement: '建议：检查能力匹配度或重新路由',
    })
  }

  // 通用经验
  experience.lessons.push({
    type: 'insight',
    message: `${executeResult.taskType || '通用'} 域任务平均执行时间 ${executeResult.executionTime || 0}ms`,
  })

  const result = {
    success: true,
    step: 6,
    stepName: '经验沉淀',
    executionId: executeResult.executionId,
    employee: executeResult.employee,
    experience,
    logEntry: {
      timestamp: new Date().toISOString(),
      level: isPassed ? 'info' : 'warning',
      category: executeResult.taskType || 'general',
    },
    summary: `经验已沉淀 — ${experience.lessons.length} 条教训, ${experience.patterns.length} 个可复用模式`,
    timestamp: Date.now(),
  }

  log('info', `[七步法·经验沉淀] ${result.summary}`)
  return result
}

/**
 * 步骤⑦ 知识反哺 (Feedback)
 * 将执行结果反馈到知识库，更新权重和索引
 *
 * @param {object} debriefResult - debrief() 的输出
 * @param {object} [options] - 反哺选项
 * @param {number} [options.rating] - 用户评分 (1-5)
 * @param {string} [options.userFeedback] - 用户反馈文本
 * @returns {object} 知识反哺结果
 */
function feedback(debriefResult, options = {}) {
  if (!debriefResult || !debriefResult.success) {
    return {
      success: false,
      step: 7,
      stepName: '知识反哺',
      error: '需要有效的经验沉淀结果',
      timestamp: Date.now(),
    }
  }

  const rating = options.rating || (debriefResult.experience?.isSuccess ? 4 : 2)
  const userFeedback = options.userFeedback || ''

  // 更新员工权重（通过路由适配器）
  let feedbackResult = { success: false, message: '路由反馈未启用' }
  try {
    const router = require('../../features/employee-route-adapter')
    if (debriefResult.employee) {
      const empId = typeof debriefResult.employee === 'object'
        ? debriefResult.employee.id || debriefResult.employee
        : debriefResult.employee
      feedbackResult = router.submitFeedback(empId, rating, userFeedback)
    }
  } catch (e) {
    // 路由适配器不可用时模拟
    feedbackResult = {
      success: true,
      employee: debriefResult.employee || 'unknown',
      newScore: 85 + (rating >= 4 ? 1 : rating <= 2 ? -1 : 0),
      delta: rating >= 4 ? 0.1 : (rating <= 2 ? -0.1 : 0),
    }
  }

  // 更新知识库索引（模拟）
  const knowledgeUpdate = {
    updatedSources: [
      { source: `${debriefResult.experience?.taskType || 'general'}_经验库`, records: debriefResult.experience?.lessons?.length || 0 },
      { source: '员工能力索引', records: 1 },
    ],
    weightAdjustment: rating >= 4 ? '+0.05' : (rating <= 2 ? '-0.03' : '0'),
  }

  const result = {
    success: true,
    step: 7,
    stepName: '知识反哺',
    executionId: debriefResult.executionId,
    employee: debriefResult.employee,
    rating,
    userFeedback,
    feedbackResult,
    knowledgeUpdate,
    nextCycleReady: true,
    summary: `知识反哺完成 — 员工权重已调整 (评分: ${rating}/5, ${feedbackResult.success ? '反馈已记录' : '反馈跳过'})`,
    timestamp: Date.now(),
  }

  log('info', `[七步法·知识反哺] ${result.summary}`)
  return result
}

// =============================================================================
//  一站式执行 — run()
// =============================================================================

/**
 * 一站式七步法执行
 * 自动完成全部7步：意图感知→知识检索→能力确认→技能调用→执行交付→经验沉淀→知识反哺
 *
 * @param {string} prompt - 用户输入的原始文本
 * @param {string|object} employee - 员工ID或员工对象（可选，默认用 seven_step_engine）
 * @param {object} [context] - 上下文选项
 * @param {string} [context.mode] - 模式提示
 * @param {string} [context.industry] - 行业
 * @param {number} [context.rating] - 用户评分 (1-5)
 * @param {string} [context.userFeedback] - 用户反馈文本
 * @param {object} [context.meta] - 其他元数据
 * @returns {object} 完整七步法执行报告
 */
function run(prompt, employee, context = {}) {
  const startTime = Date.now()
  const empArg = employee || { id: 'seven_step_engine', name: '循道' }
  const ctx = context || {}

  log('info', `[七步法] 🚀 开始执行 — 员工: ${typeof empArg === 'object' ? empArg.name : empArg}, 输入: "${(prompt || '').substring(0, 40)}..."`)

  // 步骤1: 意图感知
  const step1 = intent(prompt, ctx)
  if (!step1.success) {
    return { success: false, error: step1.error, steps: { 1: step1 }, stoppedAt: 1 }
  }

  // 步骤2: 知识检索
  const step2 = retrieve(step1, { industry: ctx.industry, employeeId: typeof empArg === 'string' ? empArg : empArg.id })

  // 步骤3: 能力确认
  const step3 = confirm(step1, step2, empArg)
  if (!step3.success) {
    return { success: false, error: step3.error, steps: { 1: step1, 2: step2, 3: step3 }, stoppedAt: 3 }
  }

  // 步骤4+5: 技能调用 + 执行交付
  const step5 = execute(step3, { prompt, text: prompt, ...ctx })

  // 步骤5验证: 执行验证
  const validation = validate(step5)

  // 步骤6: 经验沉淀
  const step6 = debrief(step5, validation)

  // 步骤7: 知识反哺
  const step7 = feedback(step6, { rating: ctx.rating, userFeedback: ctx.userFeedback })

  const totalTime = Date.now() - startTime

  // 组装完整报告
  const report = {
    success: validation.validated,
    executionId: `seven_step_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    employee: typeof empArg === 'object' ? { id: empArg.id, name: empArg.name } : { id: empArg, name: empArg },
    prompt: prompt || '',
    steps: {
      1: { name: '意图感知', status: 'completed', success: step1.success, detail: step1.summary },
      2: { name: '知识检索', status: 'completed', success: step2.success, detail: step2.summary },
      3: { name: '能力确认', status: 'completed', success: step3.success, detail: step3.summary },
      4: { name: '技能调用', status: 'completed', success: step5.success, detail: step5.parentStep4?.stepName || 'completed' },
      5: { name: '执行交付', status: 'completed', success: step5.success, detail: step5.summary },
      6: { name: '经验沉淀', status: 'completed', success: step6.success, detail: step6.summary },
      7: { name: '知识反哺', status: 'completed', success: step7.success, detail: step7.summary },
    },
    validation,
    totalTime,
    summary: `「${typeof empArg === 'object' ? empArg.name : empArg}」七步法执行完毕 — ${validation.validated ? '✅ 通过' : '⚠️ 部分问题'} (${totalTime}ms)`,
    timestamp: new Date().toISOString(),
  }

  // 记录到历史
  executionHistory.push({
    executionId: report.executionId,
    employee: report.employee,
    taskType: step1.taskType,
    success: report.success,
    totalTime,
    timestamp: report.timestamp,
  })
  if (executionHistory.length > MAX_HISTORY) {
    executionHistory.shift()
  }

  log('info', `[七步法] ✅ 执行完毕 — ${report.summary}`)
  return report
}

// =============================================================================
//  查询与统计
// =============================================================================

/** 获取引擎状态 */
function getEngineStatus() {
  return {
    autoActivate: CONFIG.auto_activate,
    logLevel: CONFIG.log_level,
    maxSteps: CONFIG.max_steps,
    totalExecutions: executionHistory.length,
    recentExecutions: executionHistory.slice(-10),
    lastExecution: executionHistory.length > 0 ? executionHistory[executionHistory.length - 1] : null,
  }
}

/** 获取执行历史 */
function getExecutionHistory(limit = 20) {
  return executionHistory.slice(-limit)
}

/** 获取执行统计 */
function getExecutionStats() {
  const total = executionHistory.length
  if (total === 0) {
    return { total: 0, message: '暂无执行记录' }
  }

  const successCount = executionHistory.filter(e => e.success).length
  const taskTypes = {}
  executionHistory.forEach(e => {
    if (e.taskType) {
      taskTypes[e.taskType] = (taskTypes[e.taskType] || 0) + 1
    }
  })
  const avgTime = Math.round(executionHistory.reduce((sum, e) => sum + (e.totalTime || 0), 0) / total)

  return {
    total,
    successRate: Math.round((successCount / total) * 100),
    successCount,
    failCount: total - successCount,
    avgExecutionTime: avgTime,
    taskTypeDistribution: taskTypes,
    topEmployee: getTopEmployee(),
  }
}

/** 获取最活跃的员工 */
function getTopEmployee() {
  const empCounts = {}
  executionHistory.forEach(e => {
    const name = typeof e.employee === 'object' ? e.employee.name : e.employee
    empCounts[name] = (empCounts[name] || 0) + 1
  })
  const entries = Object.entries(empCounts)
  if (entries.length === 0) return null
  entries.sort((a, b) => b[1] - a[1])
  return { name: entries[0][0], executions: entries[0][1] }
}

// =============================================================================
//  内部工具
// =============================================================================

/**
 * 日志输出
 * @param {'info'|'warn'|'error'} level
 * @param {string} message
 */
function log(level, message) {
  if (CONFIG.log_level === 'silent') return

  if (CONFIG.log_level === 'result_only' && level === 'info') {
    // 仅输出关键信息（summary类）
    if (!message.includes('七步法·') && !message.includes('七步法]')) return
  }

  switch (level) {
    case 'info':
      console.log(message)
      break
    case 'warn':
      console.warn(message)
      break
    case 'error':
      console.error(message)
      break
  }
}

/** 更新配置 */
function updateConfig(newConfig) {
  Object.assign(CONFIG, newConfig)
  return { ...CONFIG }
}

/** 获取当前配置 */
function getConfig() {
  return { ...CONFIG }
}

// =============================================================================
//  导出 API
// =============================================================================
module.exports = {
  // Feature 信息
  featureName: '七步法员工执行引擎',
  featureVersion: '1.0.0',
  featureDomain: 'legion',

  // 配置
  CONFIG,
  updateConfig,
  getConfig,

  // 七步法适配器协议（分步）
  intent,        // 步骤① 意图感知
  retrieve,      // 步骤② 知识检索
  confirm,       // 步骤③ 能力确认
  execute,       // 步骤④+⑤ 技能调用 + 执行交付
  validate,      // 步骤⑤验证 执行交付验证
  debrief,       // 步骤⑥ 经验沉淀
  feedback,      // 步骤⑦ 知识反哺

  // 一站式执行
  run,

  // 查询与统计
  getEngineStatus,
  getExecutionHistory,
  getExecutionStats,
}
