/**
 * 统一数据服务层
 * 支持Mock/真实API切换
 * 
 * 快速切换：
 *   通过 config/config.js 的 enableMock 字段控制
 */
const { TEST_USERS, TEST_BROCHURES, TEST_TAGS, TEST_RECOMMEND_LIST, TEST_VISITOR_STATS, TEST_TRUST_NETWORK, TEST_AI_GENERATE_TEMPLATES } = require('./test-data')
const { Logger } = require('./util')
const { userApi, brochureApi, authApi, miniappApi, matchApi, tagApi, visitorApi, trustApi, aiApi } = require('./api')
const appConfig = require('../config/config')

const MockService = {
  get USE_MOCK() {
    return appConfig.enableMock === true
  },

  async mockDelay(min = 500, max = 1500) {
    return new Promise(resolve => setTimeout(resolve, Math.random() * (max - min) + min))
  },

  async getUserProfile() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      const user = this.getTestUserByToken()
      const profile = {
        ...user.userInfo,
        memberLevel: user.memberLevel,
        tags: TEST_TAGS.slice(0, 8),
        brochure_count: TEST_BROCHURES.filter(b => b.user_id === user.user_id).length,
        match_count: TEST_RECOMMEND_LIST.length,
      }
      return { data: profile }
    }
    return userApi.getProfile()
  },

  getTestUserByToken() {
    const app = getApp()
    const token = app.globalData.token
    if (!token) {
      console.warn('[MockService] token为空，返回free用户')
      return TEST_USERS.free
    }
    for (const [level, user] of Object.entries(TEST_USERS)) {
      if (user.token === token) {
        return user
      }
    }
    console.warn('[MockService] token不匹配，返回free用户')
    return TEST_USERS.free
  },

  async login(data) {
    if (this.USE_MOCK) {
      await this.mockDelay()
      const user = TEST_USERS.gold
      const app = getApp()
      app.setLogin(user.token, user.userInfo, user.memberLevel, true)
      return {
        token: user.token,
        userInfo: user.userInfo,
        memberLevel: user.memberLevel,
      }
    }
    return authApi.login(data)
  },

  async wxMiniLogin(data) {
    if (this.USE_MOCK) {
      await this.mockDelay()
      const user = TEST_USERS.gold
      const app = getApp()
      app.setLogin(user.token, user.userInfo, user.memberLevel, true)
      return {
        token: user.token,
        userInfo: user.userInfo,
        memberLevel: user.memberLevel,
      }
    }
    return miniappApi.login(data)
  },

  async getBrochures() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { data: TEST_BROCHURES }
    }
    return brochureApi.list()
  },

  async getBrochureById(id) {
    if (this.USE_MOCK) {
      await this.mockDelay()
      const brochure = TEST_BROCHURES.find(b => b.id === id)
      return brochure || TEST_BROCHURES[0]
    }
    return brochureApi.get(id)
  },

  async createBrochure(data) {
    if (this.USE_MOCK) {
      await this.mockDelay()
      const pages = this.generatePagesFromForm(data)
      const brochure = {
        id: `b${Date.now()}`,
        ...data,
        pages,
        pages_count: pages.length,
        status: 'active',
        share_token: `share_${Date.now()}`,
        view_count: 0,
        created_at: Date.now(),
      }
      TEST_BROCHURES.unshift(brochure)
      return brochure
    }
    return brochureApi.create(data)
  },

  generatePagesFromForm(data) {
    const pages = []
    pages.push({
      type: 'cover',
      title: `${data.name || '用户'}的AI数智名片`,
      subtitle: `${data.company || ''} · ${data.title || ''}`.replace(/^ · | · $/, ''),
      avatar: data.avatar,
    })
    pages.push({
      type: 'profile',
      name: data.name || '',
      title: data.title || '',
      company: data.company || '',
      bio: data.bio || '',
      contact: {
        phone: data.phone || '',
        email: data.email || '',
        wechat: data.wechat || '',
      },
    })
    const providesLength = data.provides && data.provides.length ? data.provides.length : 0
    const needsLength = data.needs && data.needs.length ? data.needs.length : 0
    if (providesLength || needsLength) {
      pages.push({
        type: 'resources',
        provides: data.provides || [],
        needs: data.needs || [],
        purpose: data.purpose || 'partner',
      })
    }
    if (data.companyName || data.companyDesc) {
      pages.push({
        type: 'company',
        name: data.companyName || data.company || '',
        industry: data.industry || '',
        size: data.companySize || '',
        desc: data.companyDesc || '',
        development: data.development || '',
        images: data.companyImages || [],
      })
    }
    const casesLength = data.cases && data.cases.length ? data.cases.length : 0
    if (casesLength) {
      data.cases.forEach((caseItem, index) => {
        pages.push({
          type: 'case',
          index: index + 1,
          name: caseItem.name || '',
          date: caseItem.date || '',
          desc: caseItem.desc || '',
          images: caseItem.images || [],
        })
      })
    }
    pages.push({
      type: 'contact',
      name: data.name || '',
      phone: data.phone || '',
      email: data.email || '',
      wechat: data.wechat || '',
      company: data.company || '',
    })
    return pages
  },

  async deleteBrochure(id) {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { success: true }
    }
    return brochureApi.delete(id)
  },

  async getRecommendList(page = 1, size = 20) {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { data: TEST_RECOMMEND_LIST }
    }
    return matchApi.getRecommendList(page, size)
  },

  async getMatchDetail(id) {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return TEST_RECOMMEND_LIST.find(m => m.id === id) || TEST_RECOMMEND_LIST[0]
    }
    return matchApi.getMatchDetail(id)
  },

  async getTags() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { data: TEST_TAGS }
    }
    return tagApi.list()
  },

  async getVisitorStats() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { data: TEST_VISITOR_STATS }
    }
    return visitorApi.getStats()
  },

  async getTrustNetwork() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { data: TEST_TRUST_NETWORK }
    }
    return trustApi.getNetwork()
  },

  async aiChat(question, mode = 'rag', history = []) {
    if (this.USE_MOCK) {
      await this.mockDelay(1000, 2000)
      const templates = TEST_AI_GENERATE_TEMPLATES
      if (question.includes('介绍') || question.includes('简介') || question.includes('名片')) {
        return { content: templates.intro.professional.generate('用户'), type: 'text' }
      }
      if (question.includes('标签') || question.includes('关键词')) {
        return { content: '根据您的信息，推荐以下标签：\n\n🏷️ 产品经理\n🏷️ 用户增长\n🏷️ 数据分析\n🏷️ 战略规划\n\n需要调整或添加其他标签吗？', type: 'text' }
      }
      return { content: '🤖 您好！我是您的AI数智名片助手。我可以帮您：\n\n1. ✍️ 生成专业的自我介绍\n2. 🏷️ 智能推荐标签\n3. 📊 分析访客数据\n4. 🎯 匹配潜在合作伙伴\n\n有什么可以帮您的？', type: 'text' }
    }
    if (mode === 'deepseek') {
      const { deepseekApi } = require('./api')
      const messages = [
        {
          role: 'system',
          content: '你是一个专业的AI数智名片助手。请用中文回答，回答简洁、准确、有帮助。可以解答各类技术问题、商业分析、代码编写等。'
        },
        ...history.slice(-20),
        { role: 'user', content: question }
      ]
      const res = await deepseekApi.chat({ messages })
      return { content: res.reply || res.content || '', type: 'text' }
    }
    const res = await aiApi.getChat({
      message: question,
      session_id: '',
      stream: false,
    })
    return { content: res.reply || '', type: 'text' }
  },

  async aiGenerate(type, input, useDeepSeek = false) {
    if (this.USE_MOCK) {
      await this.mockDelay(1500, 3000)
      const templates = TEST_AI_GENERATE_TEMPLATES[type]
      if (templates) {
        const template = templates.professional || templates[Object.keys(templates)[0]]
        return { content: template.generate(input) }
      }
      return { content: 'AI生成内容...' }
    }
    if (useDeepSeek) {
      const { deepseekApi } = require('./api')
      return deepseekApi.generate(input)
    }
    return aiApi.generate({ type, input })
  },

  async ocrScan(imagePath) {
    if (this.USE_MOCK) {
      await this.mockDelay(1000, 2000)
      return {
        data: {
          name: '张伟',
          title: '技术总监',
          company: '腾讯科技有限公司',
          phone: '13800138000',
          email: 'zhangwei@qq.com',
          address: '深圳市南山区科技园'
        },
        confidence: 95
      }
    }
    const { aiApi } = require('./api')
    const fm = wx.getFileSystemManager()
    return new Promise((resolve, reject) => {
      fm.readFile({
        filePath: imagePath,
        encoding: 'base64',
        success(fileRes) {
          const base64Data = fileRes.data
          aiApi.getChat({
            messages: [
              { role: 'system', content: '你是一个名片OCR识别专家。请识别图片中的名片信息，提取姓名(name)、职位(title)、公司(company)、手机号(phone)、邮箱(email)、地址(address)。只返回JSON格式，不要其他文字。' },
              { role: 'user', content: '请识别这张名片上的信息。', image_base64: base64Data, image_mime: 'image/jpeg' }
            ]
          })
            .then(res => {
              const data = res.data || res
              resolve({ data, confidence: 90 })
            })
            .catch(reject)
        },
        fail: reject
      })
    })
  },

  async getRecommendations(filters = {}) {
    if (this.USE_MOCK) {
      await this.mockDelay()
      const recommendations = TEST_RECOMMEND_LIST.map(item => ({
        ...item,
        matchScore: Math.floor(Math.random() * 40) + 60,
        connected: Math.random() > 0.7,
      }))
      return { data: recommendations, list: recommendations }
    }
    return matchApi.getRecommend(filters)
  },

  async unlockContact(id) {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { success: true, data: { contactId: id } }
    }
    return matchApi.unlock(id)
  },

  async getAIConfig() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return {
        autoReply: true,
        smartRecommend: true,
        dataAnalysis: false,
        filterSensitive: true,
        timeout: 30,
        welcomeMessage: '您好！我是AI智能客服，请问有什么可以帮您的？',
      }
    }
    const { aiConfigApi } = require('./api')
    return aiConfigApi.get()
  },

  async saveAIConfig(config) {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { success: true, data: config }
    }
    const { aiConfigApi } = require('./api')
    return aiConfigApi.save(config)
  },

  async createTeam(data) {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { data: { id: `team_${Date.now()}`, ...data } }
    }
    const { teamApi } = require('./api')
    return teamApi.create(data)
  },

  async getTeamList() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { data: [] }
    }
    const { teamApi } = require('./api')
    return teamApi.list()
  },

  async membershipUpgrade(planId, period = 'monthly') {
    if (this.USE_MOCK) {
      await this.mockDelay()
      return { success: true, message: '升级成功' }
    }
    const { paymentApi } = require('./api')
    const app = getApp()
    const openid = app.globalData.openid || ''
    const tierMap = { pro: 'gold', gold: 'gold', diamond: 'diamond', enterprise: 'board' }
    const tier = tierMap[planId] || planId
    const payRes = await paymentApi.createOrder({
      tier,
      channel: 'wechat',
      openid,
    })
    if (payRes && payRes.pay_info) {
      return {
        success: true,
        pay_params: payRes.pay_info,
        order_no: payRes.order_no,
      }
    }
    throw new Error(payRes?.detail || '支付创建失败')
  },

  async getMembershipStatus() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      const user = this.getTestUserByToken()
      return {
        data: {
          tier: user.memberLevel,
          level: user.memberLevel,
          expire_at: '',
        }
      }
    }
    const { membershipApi } = require('./api')
    return membershipApi.getStatus()
  },

  async getMembershipUsage() {
    if (this.USE_MOCK) {
      await this.mockDelay()
      const user = this.getTestUserByToken()
      const cardCount = TEST_BROCHURES.filter(b => b.user_id === user.user_id).length
      const limits = {
        free: { card_limit: 1, ocr_limit: 3 },
        gold: { card_limit: 10, ocr_limit: 100 },
        diamond: { card_limit: 100, ocr_limit: 1000 },
        board: { card_limit: 999, ocr_limit: 9999 },
      }
      const limit = limits[user.memberLevel] || limits.free
      return {
        data: {
          card_count: cardCount,
          card_limit: limit.card_limit,
          ocr_count: 0,
          ocr_limit: limit.ocr_limit,
          visitor_count: 0,
        }
      }
    }
    const { membershipApi } = require('./api')
    return membershipApi.getUsageStats()
  },
}

module.exports = { MockService }