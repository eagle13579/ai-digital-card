/**
 * Mock数据服务层
 * AI数智名片 - 微信小程序
 * 
 * 纯Mock数据逻辑，与真实API调用完全分离。
 * 由 mockService.js 在 USE_MOCK=true 时委托调用。
 * 
 * 使用方式：
 *   const { MockData } = require('./mockData')
 *   const data = await MockData.getUserProfile()
 * 
 * 创建日期: 2026-07-13
 * 拆分自: mockService.js (原708行 → mockData.js + mockService.js)
 */
const store = require('./store')
const { Logger } = require('./util')

// =========================================================================
// 测试数据导入
// =========================================================================
const {
  TEST_USERS,
  TEST_BROCHURES,
  TEST_TAGS,
  TEST_RECOMMEND_LIST,
  TEST_VISITOR_STATS,
  TEST_TRUST_NETWORK,
  TEST_FRIENDS_MAP,
  TEST_PLATFORMS,
  TEST_PLATFORM_MEMBERS,
  TEST_PLATFORM_APPLICATIONS,
  TEST_AI_GENERATE_TEMPLATES,
  TEST_SIX_DEGREES_NETWORK,
  TEST_SIX_DEGREES_RELATIONS,
} = require('./test-data')

// =========================================================================
// MockData — 纯Mock逻辑对象
// =========================================================================
const MockData = {

  // =======================================================================
  // 内部辅助方法
  // =======================================================================

  /**
   * 模拟网络延迟
   * @param {number} min - 最小延迟(ms)
   * @param {number} max - 最大延迟(ms)
   */
  async mockDelay(min = 100, max = 300) {
    return new Promise(resolve => setTimeout(resolve, Math.random() * (max - min) + min))
  },

  /**
   * 根据token查找测试用户
   * @returns {object} 匹配的测试用户对象（默认返回free用户）
   */
  getTestUserByToken() {
    const { token } = store.getState()
    if (!token) {
      console.warn('[MockData] token为空，返回free用户')
      return TEST_USERS.free
    }
    for (const [level, user] of Object.entries(TEST_USERS)) {
      if (user.token === token) {
        return user
      }
    }
    console.warn('[MockData] token不匹配，返回free用户')
    return TEST_USERS.free
  },

  /**
   * 根据表单数据生成名片页面结构
   * @param {object} data - 名片表单数据
   * @returns {Array} 页面数组
   */
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

  // =======================================================================
  // 用户/认证
  // =======================================================================

  /** 获取当前用户档案（Mock） */
  async getUserProfile() {
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
  },

  /** 登录（Mock） */
  async login(data) {
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
  },

  /** 微信小程序登录（Mock） */
  async wxMiniLogin(data) {
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
  },

  // =======================================================================
  // 名片（Brochure）
  // =======================================================================

  /** 获取名片列表（Mock） */
  async getBrochures() {
    await this.mockDelay()
    return { data: TEST_BROCHURES }
  },

  /** 根据ID获取名片（Mock） */
  async getBrochureById(id) {
    await this.mockDelay()
    const brochure = TEST_BROCHURES.find(b => b.id === id)
    return brochure || TEST_BROCHURES[0]
  },

  /** 创建名片（Mock） */
  async createBrochure(data) {
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
  },

  /** 删除名片（Mock） */
  async deleteBrochure(id) {
    await this.mockDelay()
    return { success: true }
  },

  // =======================================================================
  // 匹配推荐
  // =======================================================================

  /** 获取推荐列表（Mock） */
  async getRecommendList(page = 1, size = 20) {
    await this.mockDelay()
    return { data: TEST_RECOMMEND_LIST }
  },

  /** 获取匹配详情（Mock） */
  async getMatchDetail(id) {
    await this.mockDelay()
    return TEST_RECOMMEND_LIST.find(m => m.id === id) || TEST_RECOMMEND_LIST[0]
  },

  // =======================================================================
  // 标签
  // =======================================================================

  /** 获取标签列表（Mock） */
  async getTags() {
    await this.mockDelay()
    return { data: TEST_TAGS }
  },

  // =======================================================================
  // 访客统计
  // =======================================================================

  /** 获取访客统计（Mock） */
  async getVisitorStats() {
    await this.mockDelay()
    return { data: TEST_VISITOR_STATS }
  },

  // =======================================================================
  // 信任网络
  // =======================================================================

  /** 获取信任网络（Mock） */
  async getTrustNetwork() {
    await this.mockDelay()
    return { data: TEST_TRUST_NETWORK }
  },

  // =======================================================================
  // AI 智能
  // =======================================================================

  /** AI对话（Mock） */
  async aiChat(question) {
    await this.mockDelay(1000, 2000)
    const templates = TEST_AI_GENERATE_TEMPLATES
    if (question.includes('介绍') || question.includes('简介') || question.includes('名片')) {
      return { content: templates.intro.professional.generate('用户'), type: 'text' }
    }
    if (question.includes('标签') || question.includes('关键词')) {
      return { content: '根据您的信息，推荐以下标签：\n\n🏷️ 产品经理\n🏷️ 用户增长\n🏷️ 数据分析\n🏷️ 战略规划\n\n需要调整或添加其他标签吗？', type: 'text' }
    }
    return { content: '🤖 您好！我是您的AI数智名片助手。我可以帮您：\n\n1. ✍️ 生成专业的自我介绍\n2. 🏷️ 智能推荐标签\n3. 📊 分析访客数据\n4. 🎯 匹配潜在合作伙伴\n\n有什么可以帮您的？', type: 'text' }
  },

  /** AI生成内容（Mock） */
  async aiGenerate(type, input) {
    await this.mockDelay(1500, 3000)
    const templates = TEST_AI_GENERATE_TEMPLATES[type]
    if (templates) {
      const template = templates.professional || templates[Object.keys(templates)[0]]
      return { content: template.generate(input) }
    }
    return { content: 'AI生成内容...' }
  },

  // =======================================================================
  // 资源平台
  // =======================================================================

  /** 发布资源（Mock） */
  async createResource(formData) {
    await this.mockDelay(800, 1200)
    Logger.info('资源平台', 'Mock发布资源', formData)
    return { success: true, message: '发布成功，等待审核', data: { id: Date.now(), ...formData } }
  },

  // =======================================================================
  // 好友列表
  // =======================================================================

  /** 获取好友列表（Mock） */
  async getFriendsList(userId) {
    await this.mockDelay(300, 600)
    const key = userId || 'self'
    return TEST_FRIENDS_MAP[key] || []
  },

  // =======================================================================
  // BFS触达路径
  // =======================================================================

  /** 查找最短触达路径（Mock） */
  async findPath(targetUserId) {
    await this.mockDelay(100, 200)
    const { BFSFinder } = require('./bfs')
    const getFriends = async (id) => {
      const key = id === 'self' ? 'self' : id
      return TEST_FRIENDS_MAP[key] || []
    }
    const result = await BFSFinder.findPath('self', targetUserId, getFriends)
    return result
  },

  // =======================================================================
  // 平台管理
  // =======================================================================

  /** 创建平台（Mock） */
  async createPlatform(formData) {
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
  },

  /** 获取平台列表（Mock） */
  async getPlatformList() {
    await this.mockDelay(300, 500)
    return { data: TEST_PLATFORMS }
  },

  /** 获取平台详情（Mock） */
  async getPlatformDetail(platformId) {
    await this.mockDelay(300, 600)
    const platform = TEST_PLATFORMS.find(p => p.id === platformId)
    return platform || TEST_PLATFORMS[0]
  },

  /** 获取平台成员（Mock） */
  async getPlatformMembers(platformId) {
    await this.mockDelay(300, 600)
    const members = TEST_PLATFORM_MEMBERS[platformId] || []
    const roleOrder = { secretary_general: 1, secretariat: 2, member: 3 }
    members.sort((a, b) => (roleOrder[a.role] || 9) - (roleOrder[b.role] || 9))
    return { data: members }
  },

  /** 获取平台申请列表（Mock） */
  async getPlatformApplications(platformId) {
    await this.mockDelay(300, 500)
    return { data: TEST_PLATFORM_APPLICATIONS[platformId] || [] }
  },

  /** 审核申请（Mock） */
  async reviewApplication(applicationId, approved) {
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
  },

  /** 邀请成员（Mock） */
  async inviteMember(platformId, userId) {
    await this.mockDelay(500, 800)
    if (!TEST_PLATFORM_MEMBERS[platformId]) TEST_PLATFORM_MEMBERS[platformId] = []
    TEST_PLATFORM_MEMBERS[platformId].push({
      id: userId,
      name: `用户${userId}`,
      role: 'member',
      joined_at: Date.now(),
    })
    return { success: true, message: '邀请成功' }
  },

  /** 获取平台报告（Mock） */
  async getPlatformReport(platformId) {
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
  },

  /** 获取资源覆盖率（Mock） */
  async getResourceCoverage(platformId) {
    await this.mockDelay(300, 500)
    return {
      data: {
        linkableCities: Math.floor(Math.random() * 10) + 1,
        totalResources: Math.floor(Math.random() * 50) + 10,
      },
    }
  },

  /** 获取资源排名（Mock） */
  async getResourceRanking(platformId) {
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
  },

  /** 获取资源单元（Mock） */
  async getResourceUnits(platformId) {
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
  },

  /** 获取平台机会（Mock） */
  async getPlatformOpportunities(platformId) {
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
  },

  /** 加入平台（Mock） */
  async joinPlatform(platformId) {
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
  },

  // =======================================================================
  // 洞察数据
  // =======================================================================

  /** 获取洞察数据（Mock） */
  async getInsightData() {
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
  },

  // =======================================================================
  // 六度人脉
  // =======================================================================

  /** 获取六度人脉网络（Mock） */
  async getSixDegreesNetwork(userId, maxDepth = 3) {
    await this.mockDelay(300, 600)
    return { data: TEST_SIX_DEGREES_NETWORK }
  },

  /** 获取六度人脉路径（Mock） */
  async getSixDegreesPath(fromId, toId, maxDepth = 6) {
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
  },

  /** 获取六度人脉关系（Mock） */
  async getSixDegreesRelations(userId) {
    await this.mockDelay(200, 400)
    return { data: TEST_SIX_DEGREES_RELATIONS.filter(r => r.user_id === userId) }
  },

  /** 创建六度人脉关系（Mock） */
  async createSixDegreesRelation(data) {
    await this.mockDelay(300, 500)
    const newRelation = {
      id: Date.now(),
      ...data,
      created_at: Date.now(),
    }
    TEST_SIX_DEGREES_RELATIONS.push(newRelation)
    return { success: true, message: '关系创建成功', data: newRelation }
  },

  /** 更新六度人脉信任度（Mock） */
  async updateSixDegreesTrust(id, data) {
    await this.mockDelay(200, 400)
    const relation = TEST_SIX_DEGREES_RELATIONS.find(r => r.id === id)
    if (relation) {
      Object.assign(relation, data)
    }
    return { success: true, message: '信任度已更新' }
  },

  // =======================================================================
  // 组织管理
  // =======================================================================

  /** 获取组织列表（Mock） */
  async getOrganizationList() {
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
  },

  /** 获取组织详情（Mock） */
  async getOrganizationDetail(orgId) {
    await this.mockDelay(200, 400)
    const list = await this.getOrganizationList()
    return list.find(o => o.id === orgId) || list[0]
  },

  /** 获取组织成员（Mock） */
  async getOrganizationMembers(orgId) {
    await this.mockDelay(200, 400)
    return [
      { id: 1, user_id: 'u001', name: '张伟', avatar: '', phone: '', company: '科技创新有限公司', title: '产品经理', role: 'owner', joined_at: new Date().toISOString() },
      { id: 2, user_id: 'u002', name: '李娜', avatar: '', phone: '', company: '金融投资集团', title: '投资总监', role: 'admin', joined_at: new Date().toISOString() },
      { id: 3, user_id: 'u003', name: '王强', avatar: '', phone: '', company: '人工智能研究院', title: '首席技术官', role: 'member', joined_at: new Date().toISOString() },
      { id: 4, user_id: 'u004', name: '赵丽', avatar: '', phone: '', company: '互联网公司', title: '技术总监', role: 'member', joined_at: new Date().toISOString() },
      { id: 5, user_id: 'u005', name: '陈明', avatar: '', phone: '', company: '创业孵化平台', title: '孵化总监', role: 'member', joined_at: new Date().toISOString() },
    ]
  },
}

module.exports = { MockData }
