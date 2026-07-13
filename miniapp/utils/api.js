/**
 * API 接口封装
 * AI数智名片 - 微信小程序
 * 
 * 所有接口返回 Promise，成功时直接返回 data 字段（由 request.js 统一解包）。
 * 遵循 { code, message, data } 响应格式。
 * 
 * 参考: D:\AI询赋拆解\frontend\src\services\api.ts
 */
const { get, post, put, del, upload } = require('./request')

// ===== 认证模块 =====
const authApi = {
  /** 微信小程序一键登录（wx.login → code → JWT）
   *  @param {string} code - wx.login() 返回的临时 code
   *  @param {object} [userInfo={}] - wx.getUserProfile() 返回的用户信息（nickName, avatarUrl 等）
   */
  wxMiniLogin(code, userInfo = {}) {
    return post('/api/auth/wx-mini-login', { code, user_info: userInfo }, { noAuth: true })
  },

  /** 手机号 + 验证码登录（H5/备用） */
  login(data) {
    return post('/api/auth/login', data, { noAuth: true })
  },

  /** 注册 */
  register(data) {
    return post('/api/auth/register', data, { noAuth: true })
  },

  /** 登出 */
  logout() {
    return post('/api/auth/logout')
  },

  /** 获取当前用户信息 */
  getProfile() {
    return get('/api/auth/me')
  },

  /** 注销账号（永久删除所有数据，不可恢复） */
  deleteAccount() {
    return del('/api/gdpr/account')
  },
}

// ===== 小程序专用模块 (mini app) =====
const miniappApi = {
  getCards(params) {
    return get('/api/v1/miniapp/cards', params)
  },
  getQRCode(shareToken, width) {
    return get('/api/v1/miniapp/qrcode', { share_token: shareToken, width: width || 280 })
  },
  subscribe(data) {
    return post('/api/v1/miniapp/subscribe', data)
  },
  share(data) {
    return post('/api/v1/miniapp/share', data)
  },
}

// ===== 用户模块 =====
const userApi = {
  getProfile() {
    return get('/api/users/me')
  },
  updateProfile(data) {
    return put('/api/users/me', data)
  },
  getUser(userId) {
    return get(`/api/users/${userId}`)
  },
  /** 搜索用户（关键词+行业+地区筛选，分页） */
  search(params) {
    return get('/api/users/search/list', params)
  },
}

// ===== 画册(名片)模块 =====
const brochureApi = {
  list(params = {}, options = {}) {
    return get('/api/brochures', params, options)
  },
  getById(id) {
    return get(`/api/brochures/${id}`)
  },
  getByShareToken(token) {
    return get(`/api/brochures/share/${token}`, {}, { noAuth: true })
  },
  create(data) {
    return post('/api/brochures', data)
  },
  update(id, data) {
    return put(`/api/brochures/${id}`, data)
  },
  getTemplate(purpose) {
    return get(`/api/brochures/template/${purpose}`, {}, { noAuth: true })
  },
}

// ===== 标签模块 =====
const tagApi = {
  getMyTags(tagType) {
    const params = tagType ? { tag_type: tagType } : {}
    return get('/api/tags/me', params)
  },
  list() {
    return get('/api/tags')
  },
  addTags(data) {
    return post('/api/tags/me', data)
  },
  deleteTag(tagId) {
    return del(`/api/tags/me/${tagId}`)
  },
  getUserTags(userId) {
    return get(`/api/tags/users/${userId}`)
  },
}

// ===== 匹配模块 =====
const matchApi = {
  getRecommend(params) {
    return get('/api/match/recommend', params)
  },
  getRecommendList(page = 1, size = 10, options = {}) {
    return get('/api/match/recommend', { page, size }, options)
  },
  getMatchDetail(id) {
    return get(`/api/match/${id}`)
  },
  unlock(matchId) {
    return post(`/api/match/${matchId}/unlock`)
  },
}

// ===== 信任模块 =====
const trustApi = {
  getNetwork() {
    return get('/api/trust/network')
  },
  getNetworkByUserId(userId) {
    return get(`/api/trust/network/${userId}`)
  },
  addTrust(data) {
    return post('/api/trust/network', data)
  },
  removeTrust(userId) {
    return del(`/api/trust/network/${userId}`)
  },
  getScore(targetUserId) {
    return get('/api/trust/graph/score', { target_user_id: targetUserId })
  },
}

// ===== 访客模块 =====
const visitorApi = {
  getLogs(brochureId, limit) {
    return get(`/api/visitors/${brochureId}`, { limit })
  },
  logVisit(brochureId, data) {
    return post(`/api/visitors/${brochureId}/log`, data, { noAuth: true })
  },
  getStats(brochureId) {
    return get(`/api/visitors/${brochureId}/stats`)
  },
  expressInterest(brochureId, data) {
    return post(`/api/visitors/${brochureId}/interest`, data, { noAuth: true })
  },
}

// ===== AI模块 =====
const aiApi = {
  write(data) {
    return post('/api/ai/write', data)
  },
  generate(data) {
    return post('/api/ai/generate', data)
  },
  /** AI智能对话 — 发送消息，获取AI回复 */
  chat(message, history = []) {
    return post('/api/ai/chat', { message, history })
  },
}

// ===== 支付模块 =====
const paymentApi = {
  /** 获取商品/定价列表 */
  getProducts() {
    return get('/api/payment/products')
  },
  /** 创建支付订单（微信小程序内支付） */
  createOrder(tier, channel = 'wechat', openid = '') {
    return post('/api/payment/create', { tier, channel, openid })
  },
  /** 查询订单状态 */
  queryOrder(orderNo) {
    return get(`/api/payment/query/${orderNo}`)
  },
  /** 获取当前用户订单列表 */
  listOrders() {
    return get('/api/payment/orders')
  },
  /** 获取当前用户的订阅信息 */
  getCurrentSubscription() {
    return get('/api/subscription/current')
  },
}

// ===== 平台/组织管理模块 =====
const platformApi = {
  list(keyword, skip, limit) {
    const params = {}
    if (keyword) params.keyword = keyword
    if (skip !== undefined) params.skip = skip
    if (limit !== undefined) params.limit = limit
    return get('/api/business-card/platforms', params, { noAuth: true })
  },
  getById(platformId) {
    return get(`/api/business-card/platforms/${platformId}`)
  },
  update(platformId, data) {
    return put(`/api/business-card/platforms/${platformId}`, data)
  },
  getMembers(platformId) {
    return get(`/api/business-card/platforms/${platformId}/members`)
  },
  join(platformId) {
    return post(`/api/business-card/platforms/${platformId}/join`)
  },
  getReport(platformId) {
    return get(`/api/business-card/platforms/${platformId}/report`)
  },
}

// ===== 建联/社交关系模块 =====
const connectionApi = {
  request(targetUserId, message = '', source = 'platform') {
    return post('/api/business-card/connections/request', { target_user_id: targetUserId, message, source })
  },
  review(connectionId, approved) {
    return put(`/api/business-card/connections/${connectionId}/review`, { approved })
  },
  list(status) {
    const params = status ? { status } : {}
    return get('/api/business-card/connections', params)
  },
  listPending() {
    return get('/api/business-card/connections/pending')
  },
  findPath(targetUserId) {
    return get(`/api/business-card/connections/path/${targetUserId}`)
  },
}

// ===== 消息模块 =====
const messageApi = {
  /** 获取会话列表 */
  listConversations() {
    return get('/api/messages')
  },
  /** 获取某个会话的消息（分页） */
  getMessages(conversationId, page = 1, pageSize = 50) {
    return get(`/api/messages/${conversationId}`, { page, page_size: pageSize })
  },
  /** 发送消息 */
  sendMessage(receiverId, content) {
    return post('/api/messages', { receiver_id: receiverId, content })
  },
  /** 标记会话消息已读 */
  markAsRead(conversationId) {
    return post(`/api/messages/${conversationId}/read`)
  },
  /** 获取未读消息数 */
  getUnreadCount() {
    return get('/api/messages/unread/count')
  },
}

// ===== OCR扫描模块 =====
const ocrApi = {
  /** 扫描名片图片，返回结构化信息 */
  scan(filePath) {
    // 使用统一 upload 封装（走 request.js 的认证与错误处理）
    return upload('/api/ocr/scan', filePath, 'file')
  },
}

/** 获取 API base URL */
function getApiBaseUrl() {
  const store = require('./store')
  const state = store.getState()
  return state.apiBaseUrl || 'https://card.liankebao.top'
}

/** 获取 token */
function getToken() {
  const store = require('./store')
  const state = store.getState()
  return state.token || ''
}

// ===== 团队管理模块 =====
const teamApi = {
  /** 创建团队 */
  create(data) {
    return post('/api/teams', data)
  },
  /** 获取当前用户加入的所有团队 */
  list() {
    return get('/api/teams')
  },
  /** 获取团队详情 */
  getById(teamId) {
    return get(`/api/teams/${teamId}`)
  },
  /** 更新团队信息 */
  update(teamId, data) {
    return put(`/api/teams/${teamId}`, data)
  },
  /** 删除团队 */
  remove(teamId) {
    return del(`/api/teams/${teamId}`)
  },
  /** 获取团队成员列表 */
  getMembers(teamId) {
    return get(`/api/teams/${teamId}/members`)
  },
  /** 更新成员角色 */
  updateMemberRole(teamId, userId, role) {
    return put(`/api/teams/${teamId}/members/${userId}/role`, { role })
  },
  /** 更新成员职位 */
  updateMemberTitle(teamId, userId, titleInTeam) {
    return put(`/api/teams/${teamId}/members/${userId}/title`, { title_in_team: titleInTeam })
  },
  /** 移除成员 */
  removeMember(teamId, userId) {
    return del(`/api/teams/${teamId}/members/${userId}`)
  },
  /** 邀请成员 */
  inviteMember(teamId, data) {
    return post(`/api/teams/${teamId}/invites`, data)
  },
  /** 获取团队邀请列表 */
  getInvites(teamId) {
    return get(`/api/teams/${teamId}/invites`)
  },
  /** 取消邀请 */
  cancelInvite(teamId, inviteId) {
    return del(`/api/teams/${teamId}/invites/${inviteId}`)
  },
  /** 接受邀请 */
  acceptInvite(token) {
    return post(`/api/teams/invites/${token}/accept`)
  },
  /** 拒绝邀请 */
  declineInvite(token) {
    return post(`/api/teams/invites/${token}/decline`)
  },
  /** 提交审批请求 */
  createApprovalRequest(teamId, data) {
    return post(`/api/teams/${teamId}/approval-requests`, data)
  },
  /** 查看团队的审批请求列表 */
  listApprovalRequests(teamId, status) {
    const params = status ? { status } : {}
    return get(`/api/teams/${teamId}/approval-requests`, params)
  },
  /** 审批请求 */
  reviewApprovalRequest(teamId, reqId, data) {
    return put(`/api/teams/${teamId}/approval-requests/${reqId}`, data)
  },
}

// ===== 六度人脉模块 =====
const sixDegreesApi = {
  /** 获取人脉网络图谱 */
  network(userId, maxDepth = 3) {
    return get(`/api/business-card/six-degrees/${userId}/network?max_depth=${maxDepth}`)
  },
  /** 查询最短路径 */
  path(fromId, toId, maxDepth = 6) {
    return get(`/api/business-card/six-degrees/path/${fromId}/${toId}?max_depth=${maxDepth}`)
  },
  /** 获取关系列表 */
  relations(userId) {
    return get(`/api/business-card/six-degrees/relations/${userId}`)
  },
  /** 创建关系 */
  createRelation(data) {
    return post('/api/business-card/six-degrees/relations', data)
  },
  /** 更新信任度 */
  updateTrust(id, data) {
    return put(`/api/business-card/six-degrees/relations/${id}/trust`, data)
  },
}

// ===== 组织管理模块 =====
const organizationApi = {
  /** 创建组织 */
  create(data) {
    return post('/api/business-card/organizations', data)
  },
  /** 我的组织列表 */
  list() {
    return get('/api/business-card/organizations')
  },
  /** 组织详情 */
  get(id) {
    return get(`/api/business-card/organizations/${id}`)
  },
  /** 更新组织 */
  update(id, data) {
    return put(`/api/business-card/organizations/${id}`, data)
  },
  /** 删除组织 */
  delete(id) {
    return del(`/api/business-card/organizations/${id}`)
  },
  /** 成员列表 */
  members(id) {
    return get(`/api/business-card/organizations/${id}/members`)
  },
  /** 添加成员 */
  addMember(id, data) {
    return post(`/api/business-card/organizations/${id}/members`, data)
  },
  /** 移除成员 */
  removeMember(orgId, userId) {
    return del(`/api/business-card/organizations/${orgId}/members/${userId}`)
  },
  /** 邀请列表 */
  invites(id) {
    return get(`/api/business-card/organizations/${id}/invites`)
  },
  /** 创建邀请 */
  createInvite(id, data) {
    return post(`/api/business-card/organizations/${id}/invites`, data)
  },
  /** 接受邀请 */
  acceptInvite(token) {
    return post(`/api/business-card/organizations/invites/${token}/accept`)
  },
}

module.exports = {
  miniappApi,
  authApi,
  userApi,
  brochureApi,
  tagApi,
  matchApi,
  trustApi,
  visitorApi,
  aiApi,
  paymentApi,
  platformApi,
  connectionApi,
  messageApi,
  ocrApi,
  teamApi,
  sixDegreesApi,
  organizationApi,
}
