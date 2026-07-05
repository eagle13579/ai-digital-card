/**
 * 统一数据服务层
 * 支持Mock/真实API切换
 * 
 * 快速切换方法：
 *   1. 将 USE_MOCK 改为 false 即可使用真实API
 *   2. 将 USE_MOCK 改为 true 即可使用Mock数据
 */
const { TEST_USERS, TEST_BROCHURES, TEST_TAGS, TEST_RECOMMEND_LIST, TEST_VISITOR_STATS, TEST_TRUST_NETWORK, TEST_AI_GENERATE_TEMPLATES } = require('./test-data')
const { Logger } = require('./util')
const { userApi, brochureApi, authApi, miniappApi, matchApi, tagApi, visitorApi, trustApi, aiApi } = require('./api')

const MockService = {
  USE_MOCK: true,

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

  async aiChat(question) {
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
    return aiApi.write({ prompt: question })
  },

  async aiGenerate(type, input) {
    if (this.USE_MOCK) {
      await this.mockDelay(1500, 3000)
      const templates = TEST_AI_GENERATE_TEMPLATES[type]
      if (templates) {
        const template = templates.professional || templates[Object.keys(templates)[0]]
        return { content: template.generate(input) }
      }
      return { content: 'AI生成内容...' }
    }
    return aiApi.generate({ type, input })
  },

  // ====== 资源平台 ======
  async createResource(formData) {
    if (this.USE_MOCK) {
      await this.mockDelay(800, 1200)
      Logger.info('资源平台', 'Mock发布资源', formData)
      return { success: true, message: '发布成功，等待审核', data: { id: Date.now(), ...formData } }
    }
    // TODO: 对接真实API
    const { api } = require('./api')
    return api.post('/api/v1/resources', formData)
  },
}

module.exports = { MockService }