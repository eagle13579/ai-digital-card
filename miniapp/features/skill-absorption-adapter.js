/**
 * 产品技能吸收引擎 — AI数智名片 适配器
 * ===========================================
 * 源Feature: product-skill-absorption-engine (产品技能吸收引擎)
 * 版本:      1.0.0
 * 注入日期:  2026-07-09
 *
 * 核心能力:
 *   六步飞轮(筛选→浸泡→萃取→技能化→记忆沉淀→代码收割)
 *   五卡输出(心智模型/变量/决策/动作/代码)
 *   已验证收入300+心智模型
 *
 * 集成点:
 *   1. AI对话 → 从对话中吸收技能知识点（对应浸泡+萃取）
 *   2. 名片扫描 → 行业/职位知识自动吸收
 *   3. 人脉匹配 → 从匹配结果中吸收社交智慧
 *   4. AI内容生成 → 从生成内容中收割可复用代码/模型
 *   5. 数据洞察 → 记忆沉淀 → 五卡归档
 *
 * 用法:
 *   const SkillAbsorptionAdapter = require('../../features/skill-absorption-adapter')
 *   const absorber = new SkillAbsorptionAdapter()
 *   // 分析来源
 *   const analysis = absorber.analyze({ type: 'github', url: '...' })
 *   // 执行吸收
 *   const result = absorber.absorb(analysis)
 *   // 验证结果
 *   const validation = absorber.validate(result)
 */

const CONFIG = {
  auto_hunt: true,
  max_projects_per_cycle: 3,
  code_harvest_enabled: true,
  learning_sources: ['github', 'docs', 'rss', 'manual'],
  max_cards_per_type: 200,
}

/**
 * 五卡输出数据结构
 * 吸收完成后的五种知识卡片输出
 */
const Cards = {
  /** 心智模型 — 模式/规律/理论抽象 */
  mental_models: [],
  /** 变量 — 从知识中提取的关键变量/维度 */
  variables: [],
  /** 决策 — 已验证/可复用的决策策略 */
  decisions: [],
  /** 动作 — 可执行的行动/操作步骤 */
  actions: [],
  /** 代码 — 从项目中收割的可复用代码片段 */
  code_snippets: [],
}

/**
 * 吸收流水线状态
 */
let pipelineState = {
  currentStep: null,
  sourceQueue: [],
  history: [],
  started: null,
  completed: null,
}

// =============================================================================
//  SkillAbsorptionAdapter 类
// =============================================================================

class SkillAbsorptionAdapter {
  /**
   * 创建技能吸收适配器实例
   * @param {object} options 可选配置覆盖
   * @param {boolean} options.auto_hunt
   * @param {number}  options.max_projects_per_cycle
   * @param {boolean} options.code_harvest_enabled
   * @param {string[]} options.learning_sources
   */
  constructor(options = {}) {
    this.config = { ...CONFIG, ...options }
    this.cards = {
      mental_models: [...Cards.mental_models],
      variables: [...Cards.variables],
      decisions: [...Cards.decisions],
      actions: [...Cards.actions],
      code_snippets: [...Cards.code_snippets],
    }
    this.state = {
      currentStep: null,
      sourceQueue: [...pipelineState.sourceQueue],
      history: [],
      started: null,
      completed: null,
    }
    this._stepLabels = [
      '筛选 (Scan)',
      '浸泡 (Soak)',
      '萃取 (Extract)',
      '技能化 (Skillify)',
      '记忆沉淀 (Memorize)',
      '代码收割 (Harvest)',
    ]
  }

  // ===========================================================================
  //  1. analyze() — 分析来源并初始化吸收流程（对应筛选+浸泡）
  // ===========================================================================

  /**
   * 分析外部来源，判断吸收价值并初始化吸收流程
   * @param {object} source 来源描述
   * @param {string} source.type 来源类型 (github|docs|rss|manual|scan|chat|match)
   * @param {string} [source.url] 来源URL
   * @param {string} [source.title] 来源标题/名称
   * @param {string} [source.content] 来源内容/文本
   * @param {object} [source.meta] 附加元数据
   * @returns {object} 分析结果
   */
  analyze(source) {
    if (!source || !source.type) {
      return {
        success: false,
        message: '缺少来源类型，请提供有效的 source.type',
        recommendedSourceTypes: this.config.learning_sources,
      }
    }

    // 步骤1: 筛选 (Scan) — 判断来源是否符合学习范围
    if (!this.config.learning_sources.includes(source.type)) {
      return {
        success: false,
        message: `来源类型「${source.type}」不在允许的学习来源列表中`,
        allowed: this.config.learning_sources,
        step: '筛选 (Scan)',
      }
    }

    this.state.currentStep = '筛选 (Scan)'

    // 计算来源质量评分
    const score = this._scoreSource(source)

    // 如果 auto_hunt 关闭且评分低，跳过
    if (!this.config.auto_hunt && score < 30) {
      return {
        success: false,
        message: '来源质量评分过低且 auto_hunt 关闭，跳过吸收',
        score,
        threshold: 30,
        step: '筛选 (Scan)',
      }
    }

    // 步骤2: 浸泡 (Soak) — 初步解析来源内容
    this.state.currentStep = '浸泡 (Soak)'

    const parsed = this._parseSource(source)

    const analysis = {
      success: true,
      sourceId: `src_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      source,
      score,
      parsed,
      stepsCompleted: ['筛选 (Scan)', '浸泡 (Soak)'],
      nextStep: '萃取 (Extract)',
      readyForAbsorb: score >= 30,
      timestamp: new Date().toISOString(),
    }

    // 入队
    if (analysis.readyForAbsorb) {
      this.state.sourceQueue.push({
        ...analysis,
        enqueuedAt: new Date().toISOString(),
      })
      // 限制队列长度
      if (this.state.sourceQueue.length > this.config.max_projects_per_cycle * 2) {
        this.state.sourceQueue = this.state.sourceQueue.slice(-this.config.max_projects_per_cycle * 2)
      }
    }

    return analysis
  }

  // ===========================================================================
  //  2. absorb() — 执行完整吸收（萃取→技能化→记忆沉淀→代码收割）
  // ===========================================================================

  /**
   * 对分析过的来源执行完整吸收流程
   * @param {object|string} analysisOrId analyze() 返回的分析结果或 sourceId
   * @param {object} [context] 附加上下文（行业/领域/用途等）
   * @param {string} [context.industry] 行业
   * @param {string} [context.domain] 领域
   * @param {string} [context.purpose] 吸收目的
   * @returns {object} 吸收结果（包含五卡输出）
   */
  absorb(analysisOrId, context = {}) {
    const sourceAnalysis = this._resolveSource(analysisOrId)
    if (!sourceAnalysis) {
      return {
        success: false,
        message: '未找到可吸收的来源分析结果，请先调用 analyze()',
      }
    }

    if (!sourceAnalysis.readyForAbsorb) {
      return {
        success: false,
        message: '来源评分不足，不可吸收',
        score: sourceAnalysis.score,
        threshold: 30,
      }
    }

    const { source, parsed } = sourceAnalysis
    const { industry = '', domain = '', purpose = '' } = context
    const absorbId = `absorb_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    const steps = []

    // ===== 步骤3: 萃取 (Extract) =====
    this.state.currentStep = '萃取 (Extract)'
    const extracted = this._extractContent(source, parsed, context)
    steps.push({
      step: 3,
      name: '萃取 (Extract)',
      status: 'completed',
      detail: `提取 ${extracted.mental_models.length} 个心智模型, ${extracted.variables.length} 个变量`,
      time: Date.now(),
    })

    // ===== 步骤4: 技能化 (Skillify) =====
    this.state.currentStep = '技能化 (Skillify)'
    const skillified = this._skillify(extracted, context)
    steps.push({
      step: 4,
      name: '技能化 (Skillify)',
      status: 'completed',
      detail: `转化为 ${skillified.decisions.length} 个决策策略, ${skillified.actions.length} 个动作`,
      time: Date.now(),
    })

    // ===== 步骤5: 记忆沉淀 (Memorize) =====
    this.state.currentStep = '记忆沉淀 (Memorize)'
    const memorized = this._memorize(skillified, sourceAnalysis)
    steps.push({
      step: 5,
      name: '记忆沉淀 (Memorize)',
      status: 'completed',
      detail: `沉淀到五卡: 心智模型+${memorized.added.mental_models}, 变量+${memorized.added.variables}, 决策+${memorized.added.decisions}, 动作+${memorized.added.actions}`,
      time: Date.now(),
    })

    // ===== 步骤6: 代码收割 (Harvest) =====
    this.state.currentStep = '代码收割 (Harvest)'
    const harvested = { code_snippets: [] }
    if (this.config.code_harvest_enabled) {
      Object.assign(harvested, this._harvestCode(source, parsed, context))
      steps.push({
        step: 6,
        name: '代码收割 (Harvest)',
        status: 'completed',
        detail: `收割 ${harvested.code_snippets.length} 个代码片段`,
        time: Date.now(),
      })
    } else {
      steps.push({
        step: 6,
        name: '代码收割 (Harvest)',
        status: 'skipped',
        detail: '代码收割功能已禁用 (code_harvest_enabled=false)',
        time: Date.now(),
      })
    }

    // 合并五卡
    const mergedCards = {
      mental_models: [...extracted.mental_models, ...skillified.mental_models],
      variables: [...extracted.variables],
      decisions: [...skillified.decisions],
      actions: [...skillified.actions],
      code_snippets: harvested.code_snippets,
    }

    // 写入卡片库
    Object.keys(mergedCards).forEach(key => {
      mergedCards[key].forEach(card => {
        this.cards[key].push({
          ...card,
          absorbId,
          sourceId: sourceAnalysis.sourceId,
          timestamp: new Date().toISOString(),
        })
      })
      // 限制数量
      if (this.cards[key].length > this.config.max_cards_per_type) {
        this.cards[key] = this.cards[key].slice(-this.config.max_cards_per_type)
      }
    })

    // 完成状态
    this.state.currentStep = '完成'
    const now = new Date().toISOString()
    this.state.completed = now
    if (!this.state.started) this.state.started = now

    const result = {
      success: true,
      absorbId,
      sourceId: sourceAnalysis.sourceId,
      source: source.title || source.url || source.type,
      steps,
      cards: {
        added: {
          mental_models: mergedCards.mental_models.length,
          variables: mergedCards.variables.length,
          decisions: mergedCards.decisions.length,
          actions: mergedCards.actions.length,
          code_snippets: mergedCards.code_snippets.length,
        },
        total: this.getCardCounts(),
      },
      summary: this._buildSummary(mergedCards, steps),
      context,
      timestamp: now,
    }

    // 记录历史
    this.state.history.push({
      absorbId,
      sourceId: sourceAnalysis.sourceId,
      source: source.title || source.url || source.type,
      timestamp: now,
      cardCounts: result.cards.added,
    })

    // 从队列移除已处理的来源
    this.state.sourceQueue = this.state.sourceQueue.filter(
      s => s.sourceId !== sourceAnalysis.sourceId
    )

    return result
  }

  // ===========================================================================
  //  3. validate() — 验证吸收结果的一致性与完整性
  // ===========================================================================

  /**
   * 验证吸收结果的完整性和一致性
   * @param {object} absorbResult absorb() 返回的结果
   * @returns {object} 验证报告
   */
  validate(absorbResult) {
    if (!absorbResult || !absorbResult.success) {
      return {
        valid: false,
        errors: ['无效的吸收结果：缺少 success 标志或吸收失败'],
      }
    }

    const errors = []
    const warnings = []
    const checks = {}

    // 检查1: 是否存在基本结构
    checks.hasAbsorbId = !!absorbResult.absorbId
    if (!absorbResult.absorbId) errors.push('缺少 absorbId')

    // 检查2: 是否有六步执行步骤
    checks.hasSteps = Array.isArray(absorbResult.steps) && absorbResult.steps.length >= 4
    if (!checks.hasSteps) {
      errors.push(`步骤数不足: 需要 >=4 步, 实际 ${absorbResult.steps?.length || 0} 步`)
    } else {
      const stepNames = absorbResult.steps.map(s => s.name)
      const required = ['萃取 (Extract)', '技能化 (Skillify)', '记忆沉淀 (Memorize)']
      const missing = required.filter(r => !stepNames.some(s => s.includes(r.replace(' (', '').replace(')', ''))))
      // 模糊匹配跳过括号
      const fuzzyMissing = required.filter(r => {
        const short = r.split(' (')[0]
        return !stepNames.some(s => s.includes(short))
      })
      fuzzyMissing.forEach(m => errors.push(`缺少步骤: ${m}`))
      checks.allStepsPresent = fuzzyMissing.length === 0
    }

    // 检查3: 五卡是否至少产生了一些输出
    const cards = absorbResult.cards
    checks.hasCards = !!cards && typeof cards.added === 'object'
    if (!checks.hasCards) {
      errors.push('缺少卡片输出统计 (cards)')
    } else {
      const totalCards = (cards.added.mental_models || 0)
        + (cards.added.variables || 0)
        + (cards.added.decisions || 0)
        + (cards.added.actions || 0)
        + (cards.added.code_snippets || 0)
      checks.totalCardsProduced = totalCards
      if (totalCards === 0) {
        warnings.push('吸收未产出任何知识卡片，可能来源无有效内容')
      }
    }

    // 检查4: 时间戳一致性
    checks.hasTimestamp = !!absorbResult.timestamp
    if (!absorbResult.timestamp) warnings.push('缺少时间戳')

    // 检查5: sources 完整性
    checks.hasSourceRef = !!(absorbResult.source || absorbResult.sourceId)
    if (!checks.hasSourceRef) warnings.push('缺少来源引用')

    // 检查6: 摘要
    checks.hasSummary = !!absorbResult.summary

    const valid = errors.length === 0
    const score = this._computeValidationScore(checks, errors.length, warnings.length)

    return {
      valid,
      score: Math.round(score),
      source: absorbResult.source,
      absorbId: absorbResult.absorbId,
      checks,
      errors: errors.length > 0 ? errors : undefined,
      warnings: warnings.length > 0 ? warnings : undefined,
      summary: valid
        ? `✅ 验证通过 — 共 ${checks.totalCardsProduced || 0} 张卡片, ${absorbResult.steps?.length || 0} 步执行完整`
        : `❌ 验证失败 — ${errors.length} 个错误, ${warnings.length} 个警告`,
      validatedAt: new Date().toISOString(),
    }
  }

  // ===========================================================================
  //  查询方法
  // ===========================================================================

  /** 获取五卡当前数量统计 */
  getCardCounts() {
    return {
      mental_models: this.cards.mental_models.length,
      variables: this.cards.variables.length,
      decisions: this.cards.decisions.length,
      actions: this.cards.actions.length,
      code_snippets: this.cards.code_snippets.length,
    }
  }

  /** 获取五卡详细内容（每个类型最近N条） */
  getCards(limit = 10) {
    return {
      mental_models: this.cards.mental_models.slice(-limit),
      variables: this.cards.variables.slice(-limit),
      decisions: this.cards.decisions.slice(-limit),
      actions: this.cards.actions.slice(-limit),
      code_snippets: this.cards.code_snippets.slice(-limit),
    }
  }

  /** 获取吸收流水线状态 */
  getPipelineStatus() {
    return {
      currentStep: this.state.currentStep,
      queueLength: this.state.sourceQueue.length,
      totalAbsorbed: this.state.history.length,
      config: { ...this.config },
      cards: this.getCardCounts(),
      recentHistory: this.state.history.slice(-10),
      started: this.state.started,
      completed: this.state.completed,
    }
  }

  /** 获取队列中的待吸收来源 */
  getQueue() {
    return this.state.sourceQueue.map(s => ({
      sourceId: s.sourceId,
      source: s.source.title || s.source.url || s.source.type,
      type: s.source.type,
      score: s.score,
      enqueuedAt: s.enqueuedAt,
    }))
  }

  /** 从队列中移除指定来源 */
  removeFromQueue(sourceId) {
    const before = this.state.sourceQueue.length
    this.state.sourceQueue = this.state.sourceQueue.filter(s => s.sourceId !== sourceId)
    return { removed: before - this.state.sourceQueue.length, remaining: this.state.sourceQueue.length }
  }

  /** 清空卡片库 */
  clearCards() {
    Object.keys(this.cards).forEach(key => { this.cards[key] = [] })
    return this.getCardCounts()
  }

  // ===========================================================================
  //  内部方法
  // ===========================================================================

  /**
   * 来源质量评分
   * @private
   */
  _scoreSource(source) {
    let score = 50 // 基础分

    const { type, content, url, meta } = source

    // 类型加分
    const typeScore = { github: 20, docs: 15, rss: 10, manual: 25, chat: 8, scan: 5, match: 8 }
    score += typeScore[type] || 5

    // 有内容加分
    if (content && content.length > 50) score += 10
    if (content && content.length > 500) score += 5

    // 有URL加分
    if (url) score += 5

    // 有元数据加分
    if (meta && typeof meta === 'object') {
      if (meta.stars) score += Math.min(10, meta.stars / 100)
      if (meta.language) score += 3
      if (meta.topics && meta.topics.length > 0) score += 5
    }

    return Math.min(100, Math.max(0, score))
  }

  /**
   * 解析来源内容
   * @private
   */
  _parseSource(source) {
    const { type, content = '', title = '', url = '', meta = {} } = source

    const parsed = {
      title: title || meta?.name || '未命名来源',
      type,
      wordCount: content ? content.length : 0,
      hasStructuredContent: false,
      sections: [],
      topics: meta?.topics || [],
    }

    if (content) {
      // 检测是否有结构化内容（Markdown标题/代码块/列表）
      const hasHeadings = /#{1,6}\s/.test(content)
      const hasCodeBlocks = /```[\s\S]*?```/.test(content)
      const hasLists = /^[\s]*[-*+]\s/m.test(content)
      parsed.hasStructuredContent = hasHeadings || hasCodeBlocks || hasLists

      // 提取章节
      const headingMatches = content.match(/^#{1,3}\s+(.+)$/gm)
      if (headingMatches) {
        parsed.sections = headingMatches.map(h => h.replace(/^#+\s+/, '').trim())
      }
    }

    return parsed
  }

  /**
   * 从内容中解析来源以便 resolve
   * @private
   */
  _resolveSource(analysisOrId) {
    if (typeof analysisOrId === 'object' && analysisOrId !== null) {
      return analysisOrId
    }
    // 按 sourceId 查找队列中的来源
    return this.state.sourceQueue.find(s => s.sourceId === analysisOrId) || null
  }

  /**
   * 萃取：从来源内容中提取心智模型和变量
   * @private
   */
  _extractContent(source, parsed, context) {
    const { content = '', type } = source
    const models = []
    const variables = []

    if (!content) {
      // 无文本内容时，根据类型生成基础萃取
      if (type === 'scan') {
        models.push({
          name: '名片扫描数据模型',
          description: `从名片扫描中提取的 ${source.title || '联系人'} 基础信息结构`,
          confidence: 0.85,
          source: type,
        })
        variables.push({
          name: '联系人信息',
          value: source.title || '未知',
          confidence: 0.8,
          source: type,
        })
      } else if (type === 'chat') {
        models.push({
          name: '对话模式识别',
          description: `从对话「${source.title || '未命名'}」中识别交流模式`,
          confidence: 0.6,
          source: type,
        })
      }
      return { mental_models: models, variables }
    }

    // 提取心智模型
    const modelPatterns = [
      /(模式|规律|原理|法则|效应|理论)[：:]\s*(.+?)(?=[。\n]|$)/g,
      /(核心|关键|本质|精髓)[：:]\s*(.+?)(?=[。\n]|$)/g,
      /(模型|框架|体系)[：:]\s*(.+?)(?=[。\n]|$)/g,
    ]
    modelPatterns.forEach(re => {
      let match
      while ((match = re.exec(content)) !== null) {
        models.push({
          name: match[1].trim(),
          description: match[2].trim().substring(0, 200),
          evidence: content.substring(Math.max(0, match.index - 30), match.index + match[0].length + 30),
          confidence: 0.7,
          source: type,
        })
      }
    })

    // 提取变量
    const varPattern = /(['"」】]?)([\u4e00-\u9fa5\w\s]{2,30}?)\1[:：是](.+?)(?=[。，；\n]|$)/g
    let match
    while ((match = varPattern.exec(content)) !== null) {
      const name = match[2].trim()
      const value = match[3].trim()
      if (name && value && name.length > 1 && value.length > 1) {
        variables.push({
          name,
          value: value.substring(0, 100),
          confidence: 0.65,
          source: type,
        })
      }
    }

    // 如果什么都没提取到，从标题/章节生成
    if (models.length === 0 && parsed.sections.length > 0) {
      parsed.sections.forEach(section => {
        if (section.length > 2 && section.length < 50) {
          models.push({
            name: section,
            description: `从章节标题提取的知识点: ${section}`,
            confidence: 0.5,
            source: type,
          })
        }
      })
    }

    return {
      mental_models: models.slice(0, 5),
      variables: variables.slice(0, 8),
    }
  }

  /**
   * 技能化：将萃取内容转化为决策策略和可执行动作
   * @private
   */
  _skillify(extracted, context) {
    const decisions = []
    const actions = []
    const mentalModels = extracted.mental_models || []
    const variables = extracted.variables || []

    // 从心智模型生成决策策略
    mentalModels.forEach(model => {
      decisions.push({
        hypothesis: `运用「${model.name}」模式: ${model.description?.substring(0, 100)}`,
        evidence: model.evidence || '从来源萃取',
        confidence: model.confidence || 0.6,
        status: 'pending',
        domain: context.domain || '通用',
      })

      actions.push({
        description: `验证并应用「${model.name}」心智模型到当前场景`,
        priority: model.confidence > 0.7 ? 'high' : 'medium',
        status: 'pending',
        relatedModel: model.name,
      })
    })

    // 从变量生成动作
    variables.forEach(v => {
      actions.push({
        description: `记录变量「${v.name}」的值为「${v.value?.substring(0, 50)}」并关注变化`,
        priority: 'medium',
        status: 'pending',
        relatedVariable: v.name,
      })
    })

    // 行业上下文增强
    if (context.industry) {
      decisions.push({
        hypothesis: `在 ${context.industry} 行业中应用本来源的知识`,
        evidence: `上下文行业: ${context.industry}`,
        confidence: 0.5,
        status: 'pending',
        domain: context.industry,
      })
    }

    return {
      mental_models: mentalModels,
      decisions: decisions.slice(0, 5),
      actions: actions.slice(0, 8),
    }
  }

  /**
   * 记忆沉淀：将技能化结果写入五卡仓库
   * @private
   */
  _memorize(skillified, sourceAnalysis) {
    const added = { mental_models: 0, variables: 0, decisions: 0, actions: 0, code_snippets: 0 }

    // 写入心智模型卡
    skillified.mental_models.forEach(model => {
      this.cards.mental_models.push({
        id: `mm_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        type: 'mental_model',
        name: model.name,
        description: model.description,
        evidence: model.evidence,
        confidence: model.confidence,
        source: sourceAnalysis.sourceId,
        sourceType: sourceAnalysis.source?.type,
        createdAt: new Date().toISOString(),
      })
      added.mental_models++
    })

    // 写入变量卡
    if (sourceAnalysis.parsed && sourceAnalysis.parsed.topics) {
      sourceAnalysis.parsed.topics.forEach(topic => {
        this.cards.variables.push({
          id: `var_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
          type: 'variable',
          name: topic,
          value: '',
          confidence: 0.5,
          source: sourceAnalysis.sourceId,
          createdAt: new Date().toISOString(),
        })
        added.variables++
      })
    }

    // 写入决策卡
    skillified.decisions.forEach(d => {
      this.cards.decisions.push({
        id: `dec_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        type: 'decision',
        hypothesis: d.hypothesis,
        evidence: d.evidence,
        confidence: d.confidence,
        status: d.status,
        domain: d.domain,
        source: sourceAnalysis.sourceId,
        createdAt: new Date().toISOString(),
      })
      added.decisions++
    })

    // 写入动作卡
    skillified.actions.forEach(a => {
      this.cards.actions.push({
        id: `act_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        type: 'action',
        description: a.description,
        priority: a.priority,
        status: a.status,
        relatedModel: a.relatedModel,
        relatedVariable: a.relatedVariable,
        source: sourceAnalysis.sourceId,
        createdAt: new Date().toISOString(),
      })
      added.actions++
    })

    return { added }
  }

  /**
   * 代码收割：从来源中提取代码片段
   * @private
   */
  _harvestCode(source, parsed, context) {
    const snippets = []
    const { content = '', url = '' } = source

    if (!content) return { code_snippets: snippets }

    // 提取代码块
    const codeBlockPattern = /```(\w*)\n([\s\S]*?)```/g
    let match
    while ((match = codeBlockPattern.exec(content)) !== null) {
      const language = match[1] || 'text'
      const code = match[2].trim()
      if (code.length > 10) {
        snippets.push({
          id: `code_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
          language,
          code: code.substring(0, 1000),
          lines: code.split('\n').length,
          source: source.title || url || 'unknown',
          purpose: '从来源自动收割',
          confidence: 0.8,
        })
      }
    }

    // 提取内联代码
    if (snippets.length === 0) {
      const inlinePattern = /`([^`]{10,})`/g
      while ((match = inlinePattern.exec(content)) !== null) {
        snippets.push({
          id: `code_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
          language: 'inline',
          code: match[1].substring(0, 500),
          lines: 1,
          source: source.title || url || 'unknown',
          purpose: '内联代码片段',
          confidence: 0.6,
        })
      }
    }

    // 写入卡片库
    snippets.forEach(s => {
      this.cards.code_snippets.push({
        ...s,
        type: 'code_snippet',
        createdAt: new Date().toISOString(),
      })
    })

    return { code_snippets: snippets.slice(0, 10) }
  }

  /**
   * 构建吸收摘要
   * @private
   */
  _buildSummary(cards, steps) {
    const totalCards = cards.mental_models.length + cards.variables.length
      + cards.decisions.length + cards.actions.length + cards.code_snippets.length
    const completedSteps = steps.filter(s => s.status === 'completed').length
    const skippedSteps = steps.filter(s => s.status === 'skipped').length

    let parts = [`完成 ${completedSteps}/${steps.length} 步`]
    if (cards.mental_models.length > 0) parts.push(`${cards.mental_models.length} 个心智模型`)
    if (cards.decisions.length > 0) parts.push(`${cards.decisions.length} 个决策策略`)
    if (cards.actions.length > 0) parts.push(`${cards.actions.length} 个动作`)
    if (cards.code_snippets.length > 0) parts.push(`${cards.code_snippets.length} 段代码`)
    if (skippedSteps > 0) parts.push(`${skippedSteps} 步跳过`)

    return `六步飞轮吸收完成 — ${parts.join(' · ')}`
  }

  /**
   * 计算验证评分
   * @private
   */
  _computeValidationScore(checks, errorCount, warningCount) {
    let score = 100
    if (!checks.hasAbsorbId) score -= 20
    if (!checks.hasSteps) score -= 20
    if (!checks.hasCards) score -= 20
    if (!checks.hasTimestamp) score -= 10
    if (!checks.hasSourceRef) score -= 5
    if (errorCount > 0) score -= errorCount * 10
    if (warningCount > 0) score -= warningCount * 5
    if (checks.totalCardsProduced === 0) score -= 15
    return Math.max(0, score)
  }
}

// =============================================================================
//  便捷函数（无需实例化即可使用）
// =============================================================================

/** 创建并快速执行一次完整吸收 */
function quickAbsorb(source, context = {}) {
  const adapter = new SkillAbsorptionAdapter()
  const analysis = adapter.analyze(source)
  if (!analysis.success) return analysis
  return adapter.absorb(analysis, context)
}

/** 获取全局卡片计数（默认实例） */
let _defaultInstance = null
function getDefaultInstance() {
  if (!_defaultInstance) {
    _defaultInstance = new SkillAbsorptionAdapter()
  }
  return _defaultInstance
}

// =============================================================================
//  导出 API
// =============================================================================
module.exports = {
  // 类
  SkillAbsorptionAdapter,

  // Feature 信息
  featureName: '产品技能吸收引擎',
  featureVersion: '1.0.0',
  featureDomain: 'learning',

  // 配置
  CONFIG,
  updateConfig: (newConfig) => { Object.assign(CONFIG, newConfig) },

  // 便捷方法（使用默认实例）
  analyze: (source) => getDefaultInstance().analyze(source),
  absorb: (analysis, context) => getDefaultInstance().absorb(analysis, context),
  validate: (result) => getDefaultInstance().validate(result),
  quickAbsorb,

  // 查询
  getCardCounts: () => getDefaultInstance().getCardCounts(),
  getCards: (limit) => getDefaultInstance().getCards(limit),
  getPipelineStatus: () => getDefaultInstance().getPipelineStatus(),
  getQueue: () => getDefaultInstance().getQueue(),

  // 管理
  clearCards: () => { _defaultInstance = new SkillAbsorptionAdapter(); return { cleared: true } },
}
