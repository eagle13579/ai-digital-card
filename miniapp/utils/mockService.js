/**
 * 统一数据服务层
 * 支持Mock/真实API切换
 * 
 * 快速切换方法：
 *   1. 将 USE_MOCK 改为 false 即可使用真实API
 *   2. 将 USE_MOCK 改为 true 即可使用Mock数据
 */
const store = require('./store')
const { TEST_USERS, TEST_BROCHURES, TEST_TAGS, TEST_RECOMMEND_LIST, TEST_VISITOR_STATS, TEST_TRUST_NETWORK, TEST_FRIENDS_MAP, TEST_PLATFORMS, TEST_PLATFORM_MEMBERS, TEST_PLATFORM_APPLICATIONS, TEST_AI_GENERATE_TEMPLATES } = require('./test-data')
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
    const { token } = store.getState()
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
      store.setAuth(user.token, user.userInfo)
      if (user.memberLevel) store.updateMemberLevel(user.memberLevel)
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
      store.setAuth(user.token, user.userInfo)
      if (user.memberLevel) store.updateMemberLevel(user.memberLevel)
      return {
        token: user.token,
        userInfo: user.userInfo,
        memberLevel: user.memberLevel,
      }
    }
    return authApi.wxMiniLogin(data.code)
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

  // ====== 好友列表 ======
  async getFriendsList(userId) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 600)
      const key = userId || 'self'
      return TEST_FRIENDS_MAP[key] || []
    }
    return trustApi.getNetwork(userId)
  },

  // ====== BFS触达路径 ======
  async findPath(targetUserId) {
    if (this.USE_MOCK) {
      await this.mockDelay(500, 1000)
      const { BFSFinder } = require('./bfs')
      const getFriends = async (id) => {
        const key = id === 'self' ? 'self' : id
        return TEST_FRIENDS_MAP[key] || []
      }
      const result = await BFSFinder.findPath('self', targetUserId, getFriends)
      return result
    }
    return trustApi.getScore(targetUserId)
  },

  // ====== 平台管理 ======
  async createPlatform(formData) {
    if (this.USE_MOCK) {
      await this.mockDelay(800, 1200)
      const newPlatform = {
        id: `p${Date.now()}`,
        ...formData,
        creator_id: this.getTestUserByToken().user_id,
        created_at: Date.now(),
        member_count: 1,
        resource_count: 0,
      }
      TEST_PLATFORMS.unshift(newPlatform)
      // 创建者自动成为秘书长
      const { userInfo } = store.getState()
      const userId = userInfo?.id || 'u001'
      const userName = userInfo?.name || '我'
      if (!TEST_PLATFORM_MEMBERS[newPlatform.id]) {
        TEST_PLATFORM_MEMBERS[newPlatform.id] = []
      }
      TEST_PLATFORM_MEMBERS[newPlatform.id].push({
        id: userId,
        name: userName,
        role: 'secretary_general',
        joined_at: Date.now(),
      })
      Logger.info('平台管理', 'Mock创建平台', newPlatform)
      return { success: true, message: '创建成功', data: newPlatform }
    }
    const { api } = require('./api')
    return api.post('/api/v1/platforms', formData)
  },

  async getPlatformList() {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 500)
      return { data: TEST_PLATFORMS }
    }
    const { api } = require('./api')
    return api.get('/api/v1/platforms')
  },

  async getPlatformDetail(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 600)
      const platform = TEST_PLATFORMS.find(p => p.id === platformId)
      return platform || TEST_PLATFORMS[0]
    }
    const { api } = require('./api')
    return api.get(`/api/v1/platforms/${platformId}`)
  },

  async getPlatformMembers(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 600)
      const members = TEST_PLATFORM_MEMBERS[platformId] || []
      // 按角色排序：秘书长 > 秘书处 > 会员
      const roleOrder = { secretary_general: 1, secretariat: 2, member: 3 }
      members.sort((a, b) => (roleOrder[a.role] || 9) - (roleOrder[b.role] || 9))
      return { data: members }
    }
    const { api } = require('./api')
    return api.get(`/api/v1/platforms/${platformId}/members`)
  },

  async getPlatformApplications(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 500)
      return { data: TEST_PLATFORM_APPLICATIONS[platformId] || [] }
    }
    const { api } = require('./api')
    return api.get(`/api/v1/platforms/${platformId}/applications`)
  },

  async reviewApplication(applicationId, approved) {
    if (this.USE_MOCK) {
      await this.mockDelay(500, 800)
      // 查找并更新申请
      for (const pid in TEST_PLATFORM_APPLICATIONS) {
        const apps = TEST_PLATFORM_APPLICATIONS[pid]
        const idx = apps.findIndex(a => a.id === applicationId)
        if (idx !== -1) {
          if (approved) {
            apps[idx].status = 'approved'
            // 添加到成员列表
            if (!TEST_PLATFORM_MEMBERS[pid]) TEST_PLATFORM_MEMBERS[pid] = []
            TEST_PLATFORM_MEMBERS[pid].push({
              id: apps[idx].user_id,
              name: apps[idx].user_name,
              role: 'member',
              joined_at: Date.now(),
            })
          } else {
            apps[idx].status = 'rejected'
          }
          break
        }
      }
      return { success: true, message: approved ? '已通过申请' : '已拒绝申请' }
    }
    const { api } = require('./api')
    return api.put(`/api/v1/applications/${applicationId}`, { approved })
  },

  async inviteMember(platformId, userId) {
    if (this.USE_MOCK) {
      await this.mockDelay(500, 800)
      if (!TEST_PLATFORM_MEMBERS[platformId]) TEST_PLATFORM_MEMBERS[platformId] = []
      TEST_PLATFORM_MEMBERS[platformId].push({
        id: userId,
        name: `用户${userId}`,
        role: 'member',
        joined_at: Date.now(),
      })
      return { success: true, message: '邀请成功' }
    }
    const { api } = require('./api')
    return api.post(`/api/v1/platforms/${platformId}/invite`, { user_id: userId })
  },

  async getPlatformReport(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(500, 800)
      const members = TEST_PLATFORM_MEMBERS[platformId] || []
      // 角色分布
      const roleDistribution = { secretary_general: 0, secretariat: 0, member: 0 }
      members.forEach(m => { roleDistribution[m.role] = (roleDistribution[m.role] || 0) + 1 })
      // 资源统计
      const platform = TEST_PLATFORMS.find(p => p.id === platformId)
      return {
        data: {
          roleDistribution,
          totalMembers: members.length,
          resourceCount: platform?.resource_count || 0,
          industries: platform?.industries || [],
        },
      }
    }
    const { api } = require('./api')
    return api.get(`/api/v1/platforms/${platformId}/report`)
  },
}

module.exports = MockService
module.exports.MockService = MockService  // 兼容 { MockService } 解构导入