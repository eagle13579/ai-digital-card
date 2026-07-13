/**
 * 统一数据服务层
 * 支持Mock/真实API切换
 * 
 * 快速切换方法：
 *   1. 将 USE_MOCK 改为 false 即可使用真实API
 *   2. 将 USE_MOCK 改为 true 即可使用Mock数据
 */
const store = require('./store')
const { TEST_USERS, TEST_BROCHURES, TEST_TAGS, TEST_RECOMMEND_LIST, TEST_VISITOR_STATS, TEST_TRUST_NETWORK, TEST_FRIENDS_MAP, TEST_PLATFORMS, TEST_PLATFORM_MEMBERS, TEST_PLATFORM_APPLICATIONS, TEST_AI_GENERATE_TEMPLATES, TEST_SIX_DEGREES_NETWORK, TEST_SIX_DEGREES_RELATIONS } = require('./test-data')
const { Logger } = require('./util')
const { get, post, put, del } = require('./request')
const { userApi, brochureApi, authApi, miniappApi, matchApi, tagApi, visitorApi, trustApi, aiApi, sixDegreesApi, organizationApi } = require('./api')

const MockService = {
  USE_MOCK: true,

  async mockDelay(min = 100, max = 300) {
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
        is_new: true,
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
        is_new: true,
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
    return post('/api/v1/resources', formData)
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
      await this.mockDelay(100, 200)
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
    return post('/api/v1/platforms', formData)
  },

  async getPlatformList() {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 500)
      return { data: TEST_PLATFORMS }
    }
    return get('/api/v1/platforms')
  },

  async getPlatformDetail(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 600)
      const platform = TEST_PLATFORMS.find(p => p.id === platformId)
      return platform || TEST_PLATFORMS[0]
    }
    return get(`/api/v1/platforms/${platformId}`)
  },

  async getPlatformMembers(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 600)
      const members = TEST_PLATFORM_MEMBERS[platformId] || []
      const roleOrder = { secretary_general: 1, secretariat: 2, member: 3 }
      members.sort((a, b) => (roleOrder[a.role] || 9) - (roleOrder[b.role] || 9))
      return { data: members }
    }
    return get(`/api/v1/platforms/${platformId}/members`)
  },

  async getPlatformApplications(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 500)
      return { data: TEST_PLATFORM_APPLICATIONS[platformId] || [] }
    }
    return get(`/api/v1/platforms/${platformId}/applications`)
  },

  async reviewApplication(applicationId, approved) {
    if (this.USE_MOCK) {
      await this.mockDelay(500, 800)
      for (const pid in TEST_PLATFORM_APPLICATIONS) {
        const apps = TEST_PLATFORM_APPLICATIONS[pid]
        const idx = apps.findIndex(a => a.id === applicationId)
        if (idx !== -1) {
          if (approved) {
            apps[idx].status = 'approved'
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
    return put(`/api/v1/applications/${applicationId}`, { approved })
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
    return post(`/api/v1/platforms/${platformId}/invite`, { user_id: userId })
  },

  async getPlatformReport(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(500, 800)
      const members = TEST_PLATFORM_MEMBERS[platformId] || []
      const roleDistribution = { secretary_general: 0, secretariat: 0, member: 0 }
      members.forEach(m => { roleDistribution[m.role] = (roleDistribution[m.role] || 0) + 1 })
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
    return get(`/api/v1/platforms/${platformId}/report`)
  },

  async getProfile() {
    return this.getUserProfile()
  },

  async getResourceCoverage(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 500)
      return {
        data: {
          linkableCities: Math.floor(Math.random() * 10) + 1,
          totalResources: Math.floor(Math.random() * 50) + 10,
        },
      }
    }
    return get(`/api/v1/platforms/${platformId}/coverage`)
  },

  async getResourceRanking(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 500)
      const ranking = []
      for (let i = 0; i < 5; i++) {
        ranking.push({
          rank: i + 1,
          resourceName: ['技术资源', '人才资源', '资金资源', '渠道资源', '市场资源'][i],
          count: Math.floor(Math.random() * 100) + 10,
        })
      }
      return { data: ranking }
    }
    return get(`/api/v1/platforms/${platformId}/ranking`)
  },

  async getResourceUnits(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 500)
      const units = []
      for (let i = 0; i < 4; i++) {
        units.push({
          id: `ru${i + 1}`,
          name: ['技术中心', '研发部', '市场部', '运营部'][i],
          resource_count: Math.floor(Math.random() * 20) + 5,
          status: ['active', 'active', 'active', 'pending'][i],
        })
      }
      return { data: units }
    }
    return get(`/api/v1/platforms/${platformId}/resource-units`)
  },

  async getPlatformOpportunities(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 500)
      const opportunities = []
      for (let i = 0; i < 3; i++) {
        opportunities.push({
          id: `opp${i + 1}`,
          title: ['战略合作机会', '技术对接机会', '市场拓展机会'][i],
          desc: '平台内优质合作机会，点击查看详情',
          status: 'active',
          created_at: Date.now() - i * 86400000,
        })
      }
      return { data: opportunities }
    }
    return get(`/api/v1/platforms/${platformId}/opportunities`)
  },

  async joinPlatform(platformId) {
    if (this.USE_MOCK) {
      await this.mockDelay(500, 800)
      const platform = TEST_PLATFORMS.find(p => p.id === platformId)
      if (!platform) return { success: false, message: '平台不存在' }

      const { userInfo } = store.getState()
      const userId = userInfo?.id || `u${Date.now()}`
      const userName = userInfo?.name || '用户'

      if (!TEST_PLATFORM_MEMBERS[platformId]) TEST_PLATFORM_MEMBERS[platformId] = []
      TEST_PLATFORM_MEMBERS[platformId].push({
        id: userId,
        name: userName,
        role: 'member',
        joined_at: Date.now(),
      })

      return { success: true, message: '加入成功' }
    }
    return post(`/api/v1/platforms/${platformId}/join`)
  },

  async getInsightData() {
    if (this.USE_MOCK) {
      await this.mockDelay(500, 1000)
      return {
        visits: {
          total_visits: 1256,
          today_visits: 45,
          week_over_week: 12.5,
          weeklyTrend: [32, 45, 38, 52, 48, 65, 45],
        },
        matches: {
          total_matches: 89,
          today_matches: 5,
          week_over_week: 8.3,
        },
        conversions: {
          total_conversions: 156,
          conversion_rate: 12.4,
          week_over_week: 2.1,
        },
      }
    }
    return aiApi.insight()
  },

  // ====== 六度人脉 ======
  async getSixDegreesNetwork(userId, maxDepth = 3) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 600)
      return { data: TEST_SIX_DEGREES_NETWORK }
    }
    return sixDegreesApi.network(userId, maxDepth)
  },

  async getSixDegreesPath(fromId, toId, maxDepth = 6) {
    if (this.USE_MOCK) {
      await this.mockDelay(500, 1000)
      // Build a realistic path from the test data
      const nodes = TEST_SIX_DEGREES_NETWORK.nodes
      const links = TEST_SIX_DEGREES_NETWORK.links
      const fromNode = nodes.find(n => n.id === fromId)
      const toNode = nodes.find(n => n.id === toId)
      if (!fromNode || !toNode) {
        return { distance: -1, path: [], message: '未找到路径' }
      }
      // Simple BFS to find shortest path
      const adj = {}
      links.forEach(l => {
        if (!adj[l.source]) adj[l.source] = []
        if (!adj[l.target]) adj[l.target] = []
        adj[l.source].push(l.target)
        adj[l.target].push(l.source)
      })
      const queue = [[fromId]]
      const visited = new Set([fromId])
      let foundPath = []
      while (queue.length > 0) {
        const path = queue.shift()
        const current = path[path.length - 1]
        if (current === toId) {
          foundPath = path
          break
        }
        const neighbors = adj[current] || []
        for (const n of neighbors) {
          if (!visited.has(n)) {
            visited.add(n)
            queue.push([...path, n])
          }
        }
      }
      if (foundPath.length > 0) {
        const pathNodes = foundPath.map(id => {
          const node = nodes.find(n => n.id === id)
          return { id, name: node ? node.name : id }
        })
        return { distance: foundPath.length - 1, path: pathNodes, message: '找到路径' }
      }
      return { distance: -1, path: [], message: '未找到路径' }
    }
    return sixDegreesApi.path(fromId, toId, maxDepth)
  },

  async getSixDegreesRelations(userId) {
    if (this.USE_MOCK) {
      await this.mockDelay(200, 400)
      return { data: TEST_SIX_DEGREES_RELATIONS.filter(r => r.user_id === userId) }
    }
    return sixDegreesApi.relations(userId)
  },

  async createSixDegreesRelation(data) {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 500)
      const newRelation = {
        id: Date.now(),
        ...data,
        created_at: Date.now(),
      }
      TEST_SIX_DEGREES_RELATIONS.push(newRelation)
      return { success: true, message: '关系创建成功', data: newRelation }
    }
    return sixDegreesApi.createRelation(data)
  },

  async updateSixDegreesTrust(id, data) {
    if (this.USE_MOCK) {
      await this.mockDelay(200, 400)
      const relation = TEST_SIX_DEGREES_RELATIONS.find(r => r.id === id)
      if (relation) {
        Object.assign(relation, data)
      }
      return { success: true, message: '信任度已更新' }
    }
    return sixDegreesApi.updateTrust(id, data)
  },

  // ====== 组织管理 ======
  async getOrganizationList() {
    if (this.USE_MOCK) {
      await this.mockDelay(300, 500)
      return [
        {
          id: 1,
          name: 'AI数智名片技术委员会',
          slug: 'ai-digital-card-tech',
          description: '负责AI数智名片产品的技术研发与标准制定',
          industry: '互联网/软件',
          size: '11-50人',
          owner_id: 1,
          member_count: 15,
          invite_count: 2,
          is_active: true,
          created_at: new Date(Date.now() - 86400000 * 45).toISOString(),
        },
        {
          id: 2,
          name: '市场合作联盟',
          slug: 'marketing-alliance',
          description: '联合市场推广与品牌合作',
          industry: '市场营销',
          size: '1-10人',
          owner_id: 2,
          member_count: 8,
          invite_count: 0,
          is_active: true,
          created_at: new Date(Date.now() - 86400000 * 20).toISOString(),
        },
        {
          id: 3,
          name: '产业创新中心',
          slug: 'industry-innovation',
          description: '推动产业数字化转型与创新合作',
          industry: '企业服务',
          size: '51-200人',
          owner_id: 1,
          member_count: 42,
          invite_count: 5,
          is_active: true,
          created_at: new Date(Date.now() - 86400000 * 60).toISOString(),
        },
      ]
    }
    return organizationApi.list()
  },

  async getOrganizationDetail(orgId) {
    if (this.USE_MOCK) {
      await this.mockDelay(200, 400)
      const list = await this.getOrganizationList()
      return list.find(o => o.id === orgId) || list[0]
    }
    return organizationApi.get(orgId)
  },

  async getOrganizationMembers(orgId) {
    if (this.USE_MOCK) {
      await this.mockDelay(200, 400)
      return [
        { id: 1, user_id: 'u001', name: '张伟', avatar: '', phone: '', company: '科技创新有限公司', title: '产品经理', role: 'owner', joined_at: new Date().toISOString() },
        { id: 2, user_id: 'u002', name: '李娜', avatar: '', phone: '', company: '金融投资集团', title: '投资总监', role: 'admin', joined_at: new Date().toISOString() },
        { id: 3, user_id: 'u003', name: '王强', avatar: '', phone: '', company: '人工智能研究院', title: '首席技术官', role: 'member', joined_at: new Date().toISOString() },
        { id: 4, user_id: 'u004', name: '赵丽', avatar: '', phone: '', company: '互联网公司', title: '技术总监', role: 'member', joined_at: new Date().toISOString() },
        { id: 5, user_id: 'u005', name: '陈明', avatar: '', phone: '', company: '创业孵化平台', title: '孵化总监', role: 'member', joined_at: new Date().toISOString() },
      ]
    }
    return organizationApi.members(orgId)
  },
}

module.exports = { MockService }