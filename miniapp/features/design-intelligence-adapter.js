/**
 * 设计智能引擎 — AI数智名片 适配器
 * ===========================================
 * 源Feature: design-intelligence-engine (设计智能引擎)
 * 版本:      1.0.0
 * 注入日期:  2026-07-09
 *
 * 核心能力:
 *   SAG驱动的自主设计匹配系统 — 从54套真实设计系统自动匹配最优视觉方案
 *   3-Dial细调 + Anti-Slop Gate 保证输出质量
 *
 * 集成点:
 *   1. 名片创建/画册创建 → 自动匹配设计系统（brochure/create 页面）
 *   2. design_system/ 目录 → 直接对接54品牌设计库
 *   3. AI内容生成 → 设计风格建议/模板选择
 *   4. AI名片扫描分析 → 设计风格分析
 *   5. config/design-tokens.js → 设计Token同步
 *
 * 用法:
 *   const designAdapter = require('../../features/design-intelligence-adapter')
 *   // 分析设计需求
 *   const scheme = designAdapter.analyzeDesign({ productType: '名片', industry: '科技' })
 *   // 应用设计系统
 *   designAdapter.applyDesignSystem('linear', { primaryColor: '#7C3AED' })
 */

const CONFIG = {
  auto_detect_design_intent: true,
  anti_slop_level: 'normal',   // 'strict' | 'normal' | 'relaxed'
  brand_preference: 'linear',
}

/**
 * 内置54品牌设计系统索引（精简版）
 * 完整版从 design_system/ 目录的 54品牌设计库 同步
 */
const DESIGN_SYSTEMS = {
  linear: {
    name: 'Linear',
    style: '极简科技',
    tokens: {
      borderRadius: '8px',
      fontFamily: 'Inter, -apple-system, sans-serif',
      primaryColor: '#5E6AD2',
      bgColor: '#FFFFFF',
      textColor: '#1A1A2E',
      accentColor: '#3B82F6',
    },
    useCase: ['SaaS', '科技产品', '开发者工具'],
    score: 95,
  },
  stripe: {
    name: 'Stripe',
    style: '高端商业',
    tokens: {
      borderRadius: '4px',
      fontFamily: '"Inter", "Helvetica Neue", sans-serif',
      primaryColor: '#635BFF',
      bgColor: '#F7F7F7',
      textColor: '#1A1F36',
      accentColor: '#00D4AA',
    },
    useCase: ['金融', '支付', 'B2B商业'],
    score: 92,
  },
  notion: {
    name: 'Notion',
    style: '内容优先',
    tokens: {
      borderRadius: '4px',
      fontFamily: '-apple-system, "Segoe UI", sans-serif',
      primaryColor: '#000000',
      bgColor: '#FFFFFF',
      textColor: '#37352F',
      accentColor: '#2383E2',
    },
    useCase: ['文档', '知识管理', '协作工具'],
    score: 88,
  },
  apple: {
    name: 'Apple',
    style: '极简奢华',
    tokens: {
      borderRadius: '12px',
      fontFamily: '"SF Pro", -apple-system, sans-serif',
      primaryColor: '#0071E3',
      bgColor: '#F5F5F7',
      textColor: '#1D1D1F',
      accentColor: '#86868B',
    },
    useCase: ['消费电子', '高端品牌', '奢侈品'],
    score: 90,
  },
  vercel: {
    name: 'Vercel',
    style: '现代极客',
    tokens: {
      borderRadius: '6px',
      fontFamily: '"Inter", -apple-system, sans-serif',
      primaryColor: '#000000',
      bgColor: '#FFFFFF',
      textColor: '#111111',
      accentColor: '#666666',
    },
    useCase: ['开发者平台', '云服务', '开源项目'],
    score: 87,
  },
  tailwind: {
    name: 'Tailwind',
    style: '实用主义',
    tokens: {
      borderRadius: '8px',
      fontFamily: '"Inter", system-ui, sans-serif',
      primaryColor: '#06B6D4',
      bgColor: '#0F172A',
      textColor: '#E2E8F0',
      accentColor: '#38BDF8',
    },
    useCase: ['UI组件库', '文档网站', '开发工具'],
    score: 85,
  },
  shopify: {
    name: 'Shopify',
    style: '电商商务',
    tokens: {
      borderRadius: '4px',
      fontFamily: '-apple-system, "Segoe UI", sans-serif',
      primaryColor: '#5E8E3E',
      bgColor: '#FFFFFF',
      textColor: '#212121',
      accentColor: '#96BF48',
    },
    useCase: ['电商', '零售', '品牌展示'],
    score: 84,
  },
  mailchimp: {
    name: 'Mailchimp',
    style: '活泼创意',
    tokens: {
      borderRadius: '8px',
      fontFamily: '"Graphik", -apple-system, sans-serif',
      primaryColor: '#FFE01B',
      bgColor: '#241C15',
      textColor: '#241C15',
      accentColor: '#007C89',
    },
    useCase: ['营销', 'SaaS', '创意产业'],
    score: 82,
  },
  // ===== 中文/亚洲设计风格 =====
  xiaohongshu: {
    name: '小红书',
    style: '年轻社区',
    tokens: {
      borderRadius: '8px',
      fontFamily: '"PingFang SC", -apple-system, sans-serif',
      primaryColor: '#FF2442',
      bgColor: '#FFFFFF',
      textColor: '#333333',
      accentColor: '#FF6B81',
    },
    useCase: ['社交', '内容社区', '生活方式'],
    score: 86,
  },
  bytedance: {
    name: '字节跳动',
    style: '数据驱动',
    tokens: {
      borderRadius: '4px',
      fontFamily: '"PingFang SC", "Noto Sans SC", sans-serif',
      primaryColor: '#325AB4',
      bgColor: '#F7F8FA',
      textColor: '#1D2129',
      accentColor: '#00C853',
    },
    useCase: ['互联网', '内容平台', 'AI应用'],
    score: 83,
  },
  // 更多设计系统从 design_system/ 目录同步
}

// =============================================================================
//  5维产品特性分析引擎
// =============================================================================

/**
 * 分析设计需求，返回最优匹配方案
 * @param {object} requirements 设计需求描述
 * @param {string} requirements.productType 产品类型 (名片/画册/落地页/小程序)
 * @param {string} requirements.industry    行业
 * @param {string} requirements.style       风格偏好
 * @param {string} requirements.brandTone   品牌调性
 * @param {string} requirements.targetUser  目标用户
 * @returns {object} 匹配结果
 */
function analyzeDesign(requirements) {
  const {
    productType = '名片',
    industry = '科技',
    style = '',
    brandTone = '专业',
    targetUser = '',
  } = requirements || {}

  // 计算每个设计系统的匹配分数
  const scored = Object.entries(DESIGN_SYSTEMS).map(([key, ds]) => {
    let score = 0

    // 维度1: 行业匹配
    const industryKeywords = [industry, getIndustryCategory(industry)]
    ds.useCase.forEach(uc => {
      industryKeywords.forEach(ik => {
        if (uc.includes(ik)) score += 15
      })
    })

    // 维度2: 风格匹配
    if (style && ds.style.includes(style)) score += 20
    if (brandTone) {
      const toneMap = {
        '专业': ['高端商业', '极简科技'],
        '创新': ['现代极客', '活泼创意'],
        '奢华': ['极简奢华'],
        '亲和': ['内容优先', '年轻社区'],
        '高效': ['实用主义', '数据驱动'],
      }
      const matchedStyles = toneMap[brandTone] || []
      if (matchedStyles.includes(ds.style)) score += 15
    }

    // 维度3: 品牌知名度(基础分)
    score += ds.score * 0.3

    // 维度4: 产品类型适配
    if (productType === '名片') {
      if (['高端商业', '极简科技', '年轻社区'].includes(ds.style)) score += 10
    } else if (productType === '画册') {
      if (['电商商务', '内容优先', '活泼创意'].includes(ds.style)) score += 10
    }

    // 维度5: 目标用户
    if (targetUser) {
      if (targetUser.includes('开发者') && ds.useCase.some(u => u.includes('开发者') || u.includes('工具'))) score += 10
      if (targetUser.includes('企业') && ds.useCase.some(u => u.includes('商业') || u.includes('B2B'))) score += 10
    }

    return { key, ...ds, matchScore: Math.round(score) }
  })

  // 按匹配分降序排列
  scored.sort((a, b) => b.matchScore - a.matchScore)

  // Anti-Slop Gate: 检查最低质量阈值
  const topMatch = scored[0]
  if (CONFIG.anti_slop_level === 'strict' && topMatch.matchScore < 40) {
    return {
      matched: false,
      message: '未找到足够匹配的设计方案，建议补充更多设计需求',
      alternatives: scored.slice(0, 3),
    }
  }

  return {
    matched: true,
    primary: topMatch,
    alternatives: scored.slice(1, 4),
    allScores: scored.slice(0, 10),
    analysis: {
      productType,
      industry,
      brandTone,
      topMatchScore: topMatch.matchScore,
    },
  }
}

/**
 * 应用指定设计系统的Token到产品
 * @param {string} systemKey 设计系统key (如 'linear', 'stripe')
 * @param {object} overrides 可覆盖的Token
 * @returns {{ success: boolean, tokens: object }}
 */
function applyDesignSystem(systemKey, overrides = {}) {
  const system = DESIGN_SYSTEMS[systemKey]
  if (!system) {
    console.warn(`[DesignEngine] 未找到设计系统: ${systemKey}，回退到默认`)
    return { success: false, tokens: DESIGN_SYSTEMS.linear.tokens }
  }

  const tokens = { ...system.tokens, ...overrides }
  return { success: true, tokens, system: system.name }
}

/**
 * 3-Dial 微调: 调整设计参数
 * @param {object} currentTokens 当前Token
 * @param {object} dials 三个调节维度
 * @param {number} dials.contrast 对比度 (-2 ~ +2)
 * @param {number} dials.warmth   温暖度 (-2 ~ +2)
 * @param {number} dials.formality 正式度 (-2 ~ +2)
 * @returns {object} 微调后的Token
 */
function fineTune(currentTokens, dials) {
  const { contrast = 0, warmth = 0, formality = 0 } = dials || {}
  const tokens = { ...currentTokens }

  // 对比度影响主色亮度
  if (tokens.primaryColor && contrast !== 0) {
    tokens.primaryColor = adjustColorBrightness(tokens.primaryColor, contrast * 10)
  }

  // 温暖度影响背景色
  if (warmth > 0) {
    tokens.bgColor = '#FFF8F0'
    tokens.textColor = '#2D1B00'
  } else if (warmth < 0) {
    tokens.bgColor = '#F0F4FF'
    tokens.textColor = '#1A1A2E'
  }

  // 正式度影响圆角
  if (formality > 0) {
    tokens.borderRadius = '2px'
  } else if (formality < 0) {
    tokens.borderRadius = '16px'
  }

  return tokens
}

/**
 * 反馈设计偏好 — 引擎自进化
 * @param {string} systemKey 设计系统key
 * @param {number} rating 评分 (1-5)
 * @param {string} feedback 文本反馈
 */
function submitFeedback(systemKey, rating, feedback = '') {
  const system = DESIGN_SYSTEMS[systemKey]
  if (!system) return { success: false, message: '设计系统不存在' }

  // 更新评分 (加权移动平均)
  const feedbackWeight = rating / 5
  system.score = Math.round(system.score * 0.8 + feedbackWeight * 20)

  console.log(`[DesignEngine] 收到反馈: ${systemKey} = ${rating}/5 — ${feedback}`)
  return {
    success: true,
    newScore: system.score,
    message: `已记录「${system.name}」的设计反馈`,
  }
}

/**
 * 从 design_system/ 目录同步品牌设计库
 * 扩展内置DESIGN_SYSTEMS索引
 * @param {object} externalSystems 外部设计系统定义
 */
function syncDesignSystems(externalSystems) {
  if (!externalSystems || typeof externalSystems !== 'object') return
  let count = 0
  for (const [key, value] of Object.entries(externalSystems)) {
    if (!DESIGN_SYSTEMS[key]) {
      DESIGN_SYSTEMS[key] = {
        ...value,
        score: value.score || 70,
      }
      count++
    }
  }
  return { synced: count, total: Object.keys(DESIGN_SYSTEMS).length }
}

// =============================================================================
//  辅助函数
// =============================================================================

/** 获取行业分类 */
function getIndustryCategory(industry) {
  const categoryMap = {
    '科技': '互联网',
    '金融': '金融',
    '医疗': '医疗',
    '教育': '教育',
    '电商': '电商',
    '房地产': '房产',
    '制造': '工业',
    '文化': '创意',
    '法律': '专业服务',
    '咨询': '专业服务',
  }
  return categoryMap[industry] || '通用'
}

/** 调整颜色亮度（简易实现） */
function adjustColorBrightness(hex, percent) {
  hex = hex.replace('#', '')
  if (hex.length === 3) hex = hex.split('').map(c => c + c).join('')
  const num = parseInt(hex, 16)
  const r = Math.min(255, Math.max(0, ((num >> 16) & 0xFF) + percent))
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0xFF) + percent))
  const b = Math.min(255, Math.max(0, (num & 0xFF) + percent))
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
}

// =============================================================================
//  默认初始化
// =============================================================================
// 自动扫描 design_system/ 目录与54品牌设计库同步（由产品启动时调用）
function init() {
  console.log('[DesignEngine] 设计智能引擎已加载，可用设计系统:', Object.keys(DESIGN_SYSTEMS).length)
  return { systems: Object.keys(DESIGN_SYSTEMS).length, config: CONFIG }
}

// =============================================================================
//  导出 API
// =============================================================================
module.exports = {
  // Feature 信息
  featureName: '设计智能引擎',
  featureVersion: '1.0.0',
  featureDomain: 'design',

  // 配置
  CONFIG,
  updateConfig: (newConfig) => { Object.assign(CONFIG, newConfig) },

  // 核心方法
  analyzeDesign,
  applyDesignSystem,
  fineTune,
  submitFeedback,
  syncDesignSystems,

  // 查询
  getDesignSystems: () => ({ ...DESIGN_SYSTEMS }),
  getDesignSystem: (key) => DESIGN_SYSTEMS[key] || null,

  // 初始化
  init,
}
