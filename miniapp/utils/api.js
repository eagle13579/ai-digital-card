/**
 * 统一API客户端 — AI数智名片 微信小程序
 * =============================================
 * 封装后端全部路由模块的API调用
 *
 * 特性:
 * - baseURL 通过 app.js globalData.apiBaseUrl 配置（开发/生产切换）
 * - 自动携带 token（从 app.globalData 读取）
 * - 超时控制、统一错误处理
 * - 上传文件支持 (uploadFile)
 *
 * 后端路径统一使用 /api/v1/ 前缀（中间件自动重写 /api/v1/xxx → /api/xxx）
 */

const { get, post, put, del, request } = require('./request')

/**
 * 获取 API baseURL
 * 优先级: app.globalData.apiBaseUrl > 默认开发地址
 */
function getBaseUrl() {
  try {
    const app = getApp()
    if (app && app.globalData && app.globalData.apiBaseUrl) {
      return app.globalData.apiBaseUrl
    }
  } catch (e) {
    // app 未初始化时使用默认值
  }
  return 'http://127.0.0.1:8002'
}

// 启动时日志 — 输出当前API地址，方便开发/生产切换验证
try {
  const env = getBaseUrl()
  console.log(`[API] 当前环境: ${env.includes('localhost') ? '开发(Development)' : '生产(Production)'}`)
  console.log(`[API] API基础地址: ${env}`)
} catch (e) {
  console.log('[API] 无法获取API地址（app未初始化）')
}

// =============================================================================
//  认证模块 (auth) — /api/auth
// =============================================================================
const authApi = {
  /** 账号密码登录 */
  login(data) {
    return post('/api/v1/auth/login', data, { noAuth: true })
  },
  /** 注册 */
  register(data) {
    return post('/api/v1/auth/register', data, { noAuth: true })
  },
  /** 退出登录 */
  logout() {
    return post('/api/v1/auth/logout')
  },
  /** 微信小程序静默登录（code → openid/session） */
  wxMiniLogin(code) {
    return post('/api/v1/auth/wx-mini-login', { code }, { noAuth: true })
  },
  /** 发送短信验证码 */
  smsCode(phone) {
    return post('/api/v1/auth/sms-code', { phone }, { noAuth: true })
  },
  /** 短信验证码登录 */
  smsLogin(phone, code) {
    return post('/api/v1/auth/sms-login', { phone, code }, { noAuth: true })
  },
  /** 获取当前用户认证信息 */
  getProfile() {
    return get('/api/v1/auth/profile')
  },
  /** 刷新 token */
  refreshToken(refreshToken) {
    return post('/api/v1/auth/refresh', { refresh_token: refreshToken }, { noAuth: true })
  },
  /** OAuth2 密码模式登录（兼容 OAuth2PasswordBearer） */
  oauthLogin(username, password) {
    return post('/api/v1/auth/login', { username, password }, { noAuth: true })
  },
}

// =============================================================================
//  用户模块 (user) — /api/users
// =============================================================================
const userApi = {
  /** 获取当前用户个人信息 */
  getProfile() {
    return get('/api/v1/users/me')
  },
  /** 更新当前用户个人信息 */
  updateProfile(data) {
    return put('/api/v1/users/me', data)
  },
  /** 获取指定用户信息 */
  getUser(userId) {
    return get(`/api/v1/users/${userId}`)
  },
  /** 获取用户列表（分页，管理员） */
  listUsers(params) {
    return get('/api/v1/users', params)
  },
}

// =============================================================================
//  画册 / 名片模块 (brochure) — /api/v1/brochures
// =============================================================================
const brochureApi = {
  /** 获取画册列表（分页） */
  list(params) {
    // 兼容 page/size → cursor/page_size 转换
    const q = { ...params }
    if (q.page !== undefined && q.size !== undefined) {
      q.page_size = q.size
      delete q.page
      delete q.size
    }
    return get('/api/v1/brochures', q)
  },
  /** 获取画册详情 */
  getById(id) {
    return get(`/api/v1/brochures/${id}`)
  },
  /** 通过分享 token 获取画册（无需登录） */
  getByShareToken(token) {
    return get(`/api/v1/brochures/share/${token}`, {}, { noAuth: true })
  },
  /** 创建画册 */
  create(data) {
    return post('/api/v1/brochures', data)
  },
  /** 更新画册 */
  update(id, data) {
    return put(`/api/v1/brochures/${id}`, data)
  },
  /** 删除画册 */
  delete(id) {
    return del(`/api/v1/brochures/${id}`)
  },
  /** 获取用途推荐模板 */
  getTemplate(purpose) {
    return get(`/api/v1/brochures/template/${purpose}`, {}, { noAuth: true })
  },
  /** 智能搜索画册 */
  smartSearch(params) {
    return post('/api/v1/brochures/smart-search', params)
  },
  /** 获取画册用途模板列表 */
  getPurposeTemplates() {
    return get('/api/v1/brochures/purpose-templates')
  },
  /** 上传画册媒体文件 */
  uploadMedia(filePath, formData) {
    return uploadFile('/api/v1/brochures/media/upload', filePath, formData)
  },
  /** 获取画册分享链接 */
  getShareLink(id) {
    return get(`/api/v1/brochures/${id}/share-link`)
  },
}

// =============================================================================
//  标签模块 (tag) — /api/tags
// =============================================================================
const tagApi = {
  /** 获取当前用户标签 */
  getMyTags(tagType) {
    const params = tagType ? { tag_type: tagType } : {}
    return get('/api/v1/tags/me', params)
  },
  /** 获取标签列表（全局） */
  list() {
    return get('/api/v1/tags')
  },
  /** 添加标签 */
  addTags(data) {
    return post('/api/v1/tags/me', data)
  },
  /** 删除标签 */
  deleteTag(tagId) {
    return del(`/api/v1/tags/me/${tagId}`)
  },
  /** 获取指定用户的标签 */
  getUserTags(userId) {
    return get(`/api/v1/tags/users/${userId}`)
  },
}

// =============================================================================
//  匹配模块 (match) — /api/match
// =============================================================================
const matchApi = {
  /** 获取推荐列表 */
  getRecommend(params) {
    return get('/api/v1/matching/recommendations', params)
  },
  /** 获取匹配列表（分页） */
  getMatches(params) {
    return get('/api/v1/matching/recommendations', params)
  },
  /** 获取匹配详情 */
  getMatchDetail(id) {
    return get(`/api/v1/match/${id}`)
  },
  /** 解锁联系方式 */
  unlock(matchId) {
    return post(`/api/v1/match/${matchId}/unlock`)
  },
  /** AI 混合推荐 */
  getHybridRecommend(cardId, params) {
    return post(`/api/v1/ai/recommend/hybrid/${cardId}`, params)
  },
  /** 触发匹配引擎（画册创建后调用，将当前用户加入匹配池） */
  triggerMatching(minScore = 0.3) {
    return post(`/api/v1/match/engine?min_score=${minScore}`)
  },
}

// =============================================================================
//  访客模块 (visitor) — /api/visitors
// =============================================================================
const visitorApi = {
  /** 获取画册访客记录 */
  getLogs(brochureId, limit) {
    return get(`/api/v1/visitors/${brochureId}`, { limit })
  },
  /** 记录访客（无需登录） */
  logVisit(brochureId, data) {
    return post(`/api/v1/visitors/${brochureId}/log`, data, { noAuth: true })
  },
  /** 获取访客统计 */
  getStats(brochureId) {
    return get(`/api/v1/visitors/${brochureId}/stats`)
  },
  /** 表达合作意向（无需登录） */
  expressInterest(brochureId, data) {
    return post(`/api/v1/visitors/${brochureId}/interest`, data, { noAuth: true })
  },
}

// =============================================================================
//  信任网络模块 (trust) — /api/trust
// =============================================================================
const trustApi = {
  /** 获取信任网络 */
  getNetwork() {
    return get('/api/v1/trust/network')
  },
  /** 添加信任关系 */
  addTrust(data) {
    return post('/api/v1/trust/network', data)
  },
  /** 移除信任关系 */
  removeTrust(userId) {
    return del(`/api/v1/trust/network/${userId}`)
  },
  /** 获取信任评分 */
  getScore(targetUserId) {
    return get('/api/v1/trust/graph/score', { target_user_id: targetUserId })
  },
}

// =============================================================================
//  AI 助手模块 (ai) — /ai/assist
// =============================================================================
const aiApi = {
  /** AI 对话聊天 (RAG会话) — 流式或非流式 */
  getChat(data) {
    return post('/api/v1/ai/chat', data)
  },
  /** AI 文案写作 */
  write(data) {
    return post('/api/v1/ai/assist/write', data)
  },
  /** AI 生成内容（名片、文案等） */
  generate(data) {
    return post('/api/v1/ai/assist/write', data)
  },
  /** AI 优化建议 */
  optimize(data) {
    return post('/api/v1/ai/assist/optimize', data)
  },
  /** DeepSeek 纯对话（非RAG，直接调用DeepSeek API） */
  deepseekChat(data) {
    return post('/api/v1/ai/deepseek/chat', data)
  },
}

// =============================================================================
//  AI 配置模块 (ai/config) — /api/v1/ai/config
// =============================================================================
const aiConfigApi = {
  /** 获取AI客服配置 */
  get() {
    return get('/api/v1/ai/config')
  },
  /** 保存AI客服配置 */
  save(data) {
    return post('/api/v1/ai/config', data)
  },
}

// =============================================================================
//  场景模块 (scene) — /api/v1/scene
// =============================================================================
const sceneApi = {
  /** AI场景分类 — 输入context/output scene_type */
  classify(context) {
    return post('/api/v1/scene/classify', { context })
  },
}

// =============================================================================
//  人脉网络模块 (network) — /api/v1/network
// =============================================================================
const networkApi = {
  /** 人脉链路径推理 — 输入from/to user_id/output paths */
  bridge(fromUserId, toUserId) {
    return post('/api/v1/network/bridge', { from_user_id: fromUserId, to_user_id: toUserId })
  },
}

// =============================================================================
//  名片编辑模块 (card/edit) — /api/v1/card/edit
// =============================================================================
const cardEditApi = {
  /** 对话式编辑意图理解 — 输入自然语言指令，输出意图摘要 */
  interpret(text, cardId) {
    return post('/api/v1/card/edit/interpret', { text, card_id: cardId })
  },
  /** 对话式编辑执行 — 确认后执行编辑操作 */
  execute(intent, cardId) {
    return post('/api/v1/card/edit/execute', { intent, card_id: cardId })
  },
}

// =============================================================================
//  推荐模块 (recommend) — /api/recommend
// =============================================================================
const recommendApi = {
  /** 个性化推荐 */
  getPersonal(params) {
    return post('/api/v1/recommend/personal', params)
  },
  /** 发现推荐（全局发现页） */
  getDiscover(params) {
    return post('/api/v1/recommend/discover', params)
  },
  /** 相似名片推荐 */
  getSimilar(params) {
    return post('/api/v1/recommend/similar', params)
  },
  /** 提交推荐反馈 */
  submitFeedback(data) {
    return post('/api/v1/recommend/feedback', data)
  },
}

// =============================================================================
//  小程序专用模块 (miniapp) — /api/business-card/cards
// =============================================================================
const miniappApi = {
  /** 小程序登录 */
  login(data) {
    return post('/api/v1/business-card/cards/login', data, { noAuth: true })
  },
  /** 获取名片列表 */
  getCards(params) {
    return get('/api/v1/business-card/cards', params)
  },
  /** 获取二维码 */
  getQRCode(shareToken, width) {
    return get('/api/v1/business-card/cards/qrcode', { share_token: shareToken, width: width || 280 })
  },
  /** 订阅通知 */
  subscribe(data) {
    return post('/api/v1/business-card/cards/subscribe', data)
  },
  /** 分享名片 */
  share(data) {
    return post('/api/v1/business-card/cards/share', data)
  },
  /** 交换名片 */
  exchange(data) {
    return post('/api/v1/business-card/exchange', data)
  },
  /** 获取推荐列表（matching 适配） */
  getRecommendations(params) {
    return get('/api/v1/matching/recommendations', params)
  },
}

// =============================================================================
//  支付模块 (payment) — /api/payment
// =============================================================================
const paymentApi = {
  /** 创建订单 */
  createOrder(data) {
    return post('/api/v1/payment/order', data)
  },
  /** 微信支付统一下单 */
  wxPay(orderNo, params) {
    return post('/api/v1/payment/wxpay', { order_no: orderNo, ...params })
  },
  /** 支付宝支付 */
  alipay(orderNo) {
    return post('/api/v1/payment/alipay', { order_no: orderNo })
  },
  /** 获取订单列表 */
  getOrders(params) {
    return get('/api/v1/payment/orders', params)
  },
  /** 查询订单状态 */
  getOrderStatus(orderNo) {
    return get(`/api/v1/payment/orders/${orderNo}/status`)
  },
  /** 支付回调通知 */
  payNotify(channel, data) {
    return post(`/api/v1/payment/${channel}/notify`, data, { noAuth: true })
  },
}

// =============================================================================
//  订阅模块 (subscription) — /api/subscription
// =============================================================================
const subscriptionApi = {
  /** 获取当前订阅信息 */
  getCurrent() {
    return get('/api/v1/subscription/current')
  },
  /** 获取套餐列表 */
  getPlans() {
    return get('/api/v1/subscription/plans')
  },
  /** 开始试用 */
  startTrial() {
    return post('/api/v1/subscription/trial')
  },
  /** 升级套餐 */
  upgrade(planId, period) {
    return post('/api/v1/subscription/upgrade', { plan_id: planId, period })
  },
  /** 降级套餐 */
  downgrade(planId) {
    return post('/api/v1/subscription/downgrade', { plan_id: planId })
  },
  /** 取消订阅 */
  cancel() {
    return post('/api/v1/subscription/cancel')
  },
}

// =============================================================================
//  消息模块 (messages) — /api/messages
// =============================================================================
const messageApi = {
  /** 获取通知列表 */
  getList(params) {
    return get('/api/v1/messages', params)
  },
  /** 标记已读 */
  markRead(messageId) {
    return post(`/api/v1/messages/${messageId}/read`)
  },
  /** 标记全部已读 */
  markAllRead() {
    return post('/api/v1/messages/read-all')
  },
  /** 获取未读消息数 */
  getUnreadCount() {
    return get('/api/v1/messages/unread-count')
  },
}

// =============================================================================
//  团队模块 (team) — /api/teams
// =============================================================================
const teamApi = {
  /** 获取团队列表 */
  getList(params) {
    return get('/api/v1/teams', params)
  },
  /** 创建团队 */
  create(data) {
    return post('/api/v1/teams', data)
  },
  /** 获取团队详情 */
  getDetail(teamId) {
    return get(`/api/v1/teams/${teamId}`)
  },
  /** 更新团队 */
  update(teamId, data) {
    return put(`/api/v1/teams/${teamId}`, data)
  },
  /** 删除团队 */
  delete(teamId) {
    return del(`/api/v1/teams/${teamId}`)
  },
  /** 获取团队成员 */
  getMembers(teamId) {
    return get(`/api/v1/teams/${teamId}/members`)
  },
  /** 邀请成员 */
  inviteMember(teamId, data) {
    return post(`/api/v1/teams/${teamId}/invite`, data)
  },
  /** 移除成员 */
  removeMember(teamId, userId) {
    return del(`/api/v1/teams/${teamId}/members/${userId}`)
  },
}

// =============================================================================
//  集成模块 (integration) — /api/integrations
// =============================================================================
const integrationApi = {
  /** 获取集成列表 */
  getList() {
    return get('/api/v1/integrations')
  },
  /** 创建集成配置 */
  create(data) {
    return post('/api/v1/integrations', data)
  },
  /** 更新集成配置 */
  update(id, data) {
    return put(`/api/v1/integrations/${id}`, data)
  },
  /** 删除集成配置 */
  delete(id) {
    return del(`/api/v1/integrations/${id}`)
  },
  /** 测试集成连接 */
  testConnection(id) {
    return post(`/api/v1/integrations/${id}/test`)
  },
}

// =============================================================================
//  会员 / 订阅模块 (membership) — /api/v1/membership
// =============================================================================
const membershipApi = {
  /** 获取当前用户会员层级与使用额度 */
  getStatus() {
    return get('/api/v1/membership/status')
  },
  /** 获取所有套餐方案 */
  getPlans() {
    return get('/api/v1/membership/plans')
  },
  /** 获取套餐定价列表 */
  getPricing() {
    return get('/api/v1/membership/pricing')
  },
  /** 升级套餐（按 planId + 周期） */
  upgrade(planId, period) {
    return post('/api/v1/membership/upgrade', { plan_id: planId, period })
  },
  /** 升级套餐（按 tier 等级，简化版） */
  upgradeByTier(tier) {
    return post('/api/v1/membership/upgrade', { tier })
  },
  /** 获取使用统计（名片数量、OCR次数、访客数等） */
  getUsageStats() {
    return get('/api/v1/membership/usage-stats')
  },
}

// =============================================================================
//  DeepSeek AI 专属模块 (deepseek) — /api/v1/ai/deepseek
// =============================================================================
const deepseekApi = {
  /** DeepSeek 多轮对话 */
  chat(messages) {
    return post('/api/v1/ai/deepseek/chat', { messages })
  },
  /** DeepSeek 深度生成（单次提示词） */
  generate(prompt) {
    return post('/api/v1/ai/deepseek/generate', { prompt, temperature: 0.7, max_tokens: 2048 })
  },
  /** DeepSeek 服务状态 */
  status() {
    return get('/api/v1/ai/deepseek/status')
  },
}

// =============================================================================
//  导出模块 (export) — /api/export
// =============================================================================
const exportApi = {
  /** 导出数据 */
  exportData(params) {
    return get('/api/v1/export', params)
  },
  /** 获取导出任务状态 */
  getTaskStatus(taskId) {
    return get(`/api/v1/export/tasks/${taskId}`)
  },
}

// =============================================================================
//  Webhook 模块 (webhook) — /api/webhooks
// =============================================================================
const webhookApi = {
  /** 获取 Webhook 订阅列表 */
  getList() {
    return get('/api/v1/webhooks')
  },
  /** 创建 Webhook 订阅 */
  create(data) {
    return post('/api/v1/webhooks', data)
  },
  /** 更新 Webhook 订阅 */
  update(id, data) {
    return put(`/api/v1/webhooks/${id}`, data)
  },
  /** 删除 Webhook 订阅 */
  delete(id) {
    return del(`/api/v1/webhooks/${id}`)
  },
  /** 触发 Webhook 测试 */
  trigger(id, data) {
    return post(`/api/v1/webhooks/${id}/trigger`, data)
  },
}

// =============================================================================
//  CRM 模块 (crm) — /api/crm
// =============================================================================
const crmApi = {
  /** ── 联系人 ── */
  createContact(data) {
    return post('/api/v1/crm/contacts', data)
  },
  getContacts(params) {
    return get('/api/v1/crm/contacts', params)
  },
  getContact(contactId) {
    return get(`/api/v1/crm/contacts/${contactId}`)
  },
  updateContact(contactId, data) {
    return put(`/api/v1/crm/contacts/${contactId}`, data)
  },
  deleteContact(contactId) {
    return del(`/api/v1/crm/contacts/${contactId}`)
  },
  getContactTimeline(contactId) {
    return get(`/api/v1/crm/contacts/${contactId}/timeline`)
  },
  /** ── 活动 ── */
  createActivity(data) {
    return post('/api/v1/crm/activities', data)
  },
  /** ── 备注 ── */
  createNote(data) {
    return post('/api/v1/crm/notes', data)
  },
  getContactNotes(contactId) {
    return get(`/api/v1/crm/contacts/${contactId}/notes`)
  },
  updateNote(noteId, data) {
    return put(`/api/v1/crm/notes/${noteId}`, data)
  },
  deleteNote(noteId) {
    return del(`/api/v1/crm/notes/${noteId}`)
  },
  /** ── 管道/交易 ── */
  getPipelineStages() {
    return get('/api/v1/crm/pipeline/stages')
  },
  getPipelineDeals() {
    return get('/api/v1/crm/pipeline/deals')
  },
  createDeal(data) {
    return post('/api/v1/crm/deals', data)
  },
  updateDealStage(dealId, stage) {
    return put(`/api/v1/crm/deals/${dealId}/stage`, { stage })
  },
  /** ── 销售预测 ── */
  getPrediction(dealId) {
    return get(`/api/v1/crm/prediction/deal/${dealId}`)
  },
  retrainPrediction() {
    return post('/api/v1/crm/prediction/retrain')
  },
  getPredictionStatus() {
    return get('/api/v1/crm/prediction/status')
  },
  /** ── 表单捕获 ── */
  getForms() {
    return get('/api/v1/crm/forms')
  },
  getForm(formId) {
    return get(`/api/v1/crm/forms/${formId}`)
  },
  createForm(data) {
    return post('/api/v1/crm/forms', data)
  },
  updateForm(formId, data) {
    return put(`/api/v1/crm/forms/${formId}`, data)
  },
  deleteForm(formId) {
    return del(`/api/v1/crm/forms/${formId}`)
  },
  getFormEmbedCode(formId) {
    return get(`/api/v1/crm/forms/${formId}/embed`)
  },
  getFormLogs(formId) {
    return get(`/api/v1/crm/forms/${formId}/logs`)
  },
  submitForm(formId, data) {
    return post(`/api/v1/crm/forms/${formId}/submit`, data, { noAuth: true })
  },
  /** ── 邮件营销 ── */
  getCampaigns() {
    return get('/api/v1/crm/campaigns')
  },
  createCampaign(data) {
    return post('/api/v1/crm/campaigns', data)
  },
  /** ── 文档 ── */
  getDocuments(params) {
    return get('/api/v1/crm/documents', params)
  },
  createDocument(data) {
    return post('/api/v1/crm/documents', data)
  },
  getDocument(docId) {
    return get(`/api/v1/crm/documents/${docId}`)
  },
  updateDocument(docId, data) {
    return put(`/api/v1/crm/documents/${docId}`, data)
  },
  deleteDocument(docId) {
    return del(`/api/v1/crm/documents/${docId}`)
  },
}

// =============================================================================
//  OAuth / SSO 模块 (oauth) — /api/v1/oauth
// =============================================================================
const oauthApi = {
  /** 获取 OAuth 提供商列表 */
  getProviders() {
    return get('/api/v1/oauth/providers')
  },
  /** 发起 OAuth 登录 */
  login(provider, redirectUri) {
    return get(`/api/v1/oauth/${provider}/login`, { redirect_uri: redirectUri })
  },
  /** OAuth 回调 */
  callback(provider, code, state) {
    return get(`/api/v1/oauth/${provider}/callback`, { code, state }, { noAuth: true })
  },
  /** 绑定第三方账号 */
  link(provider, data) {
    return post(`/api/v1/oauth/${provider}/link`, data)
  },
  /** SSO 登录 */
  ssoLogin(provider, data) {
    return post(`/api/v1/auth/sso/${provider}/login`, data, { noAuth: true })
  },
  /** SSO 回调 */
  ssoCallback(provider, code, state) {
    return get(`/api/v1/auth/sso/${provider}/callback`, { code, state }, { noAuth: true })
  },
}

// =============================================================================
//  API Key 管理 — /api/v1/api-keys
// =============================================================================
const apiKeyApi = {
  /** 获取 API Key 列表 */
  getList() {
    return get('/api/v1/api-keys')
  },
  /** 创建 API Key */
  create(data) {
    return post('/api/v1/api-keys', data)
  },
  /** 删除 API Key */
  delete(keyId) {
    return del(`/api/v1/api-keys/${keyId}`)
  },
}

// =============================================================================
//  A/B 测试模块 (ab_test) — /api/v1/ab-test
// =============================================================================
const abTestApi = {
  /** 获取实验列表 */
  getExperiments() {
    return get('/api/v1/ab-test/experiments')
  },
  /** 创建实验 */
  createExperiment(data) {
    return post('/api/v1/ab-test/experiments', data)
  },
  /** 上报实验结果 */
  report(data) {
    return post('/api/v1/ab-test/report', data)
  },
}

// =============================================================================
//  增长分析模块 (growth) — /api/v1/growth
// =============================================================================
const growthApi = {
  /** 获取核心增长指标 */
  getMetrics() {
    return get('/api/v1/growth/metrics')
  },
  /** 获取增长趋势 */
  getTrends(params) {
    return get('/api/v1/growth/trends', params)
  },
  /** 获取获客来源 */
  getSources() {
    return get('/api/v1/growth/sources')
  },
  /** 获取留存分析 */
  getRetention() {
    return get('/api/v1/growth/retention')
  },
}

// =============================================================================
//  App Store / 插件模块 — /api/v1/app-store
// =============================================================================
const appStoreApi = {
  /** 获取插件列表 */
  getPlugins(params) {
    return get('/api/v1/app-store/plugins', params)
  },
  /** 安装插件 */
  install(pluginId) {
    return post('/api/v1/app-store/install', { plugin_id: pluginId })
  },
  /** 卸载插件 */
  uninstall(pluginId) {
    return post('/api/v1/app-store/uninstall', { plugin_id: pluginId })
  },
  /** 获取排行榜 */
  getLeaderboard(params) {
    return get('/api/v1/app-store/leaderboard', params)
  },
}

// =============================================================================
//  管理员模块 (admin) — /api/v1/admin
// =============================================================================
const adminApi = {
  /** 仪表盘统计 */
  getDashboard() {
    return get('/api/v1/admin/dashboard')
  },
  /** ── 租户管理 ── */
  createTenant(data) {
    return post('/api/v1/admin/tenants', data)
  },
  getTenants(params) {
    return get('/api/v1/admin/tenants', params)
  },
}

// =============================================================================
//  开发者模块 (developer) — /api/v1/developer
// =============================================================================
const developerApi = {
  /** 获取开发者信息 */
  getProfile() {
    return get('/api/v1/developer/profile')
  },
  /** 更新开发者信息 */
  updateProfile(data) {
    return put('/api/v1/developer/profile', data)
  },
}

// =============================================================================
//  发票模块 (invoice) — /api/invoices
// =============================================================================
const invoiceApi = {
  /** 获取发票列表 */
  getList(params) {
    return get('/api/v1/invoices', params)
  },
  /** 申请开票 */
  apply(data) {
    return post('/api/v1/invoices', data)
  },
  /** 获取发票详情 */
  getDetail(invoiceId) {
    return get(`/api/v1/invoices/${invoiceId}`)
  },
}

// =============================================================================
//  知识图谱模块 (knowledge-graph) — /api/knowledge-graph
// =============================================================================
const knowledgeGraphApi = {
  /** 获取知识图谱数据 */
  getGraph(params) {
    return get('/api/v1/knowledge-graph', params)
  },
  /** 搜索知识节点 */
  searchNodes(params) {
    return get('/api/v1/knowledge-graph/search', params)
  },
  /** 获取节点详情 */
  getNode(nodeId) {
    return get(`/api/v1/knowledge-graph/nodes/${nodeId}`)
  },
}

// =============================================================================
//  i18n 国际化模块 — /api/i18n
// =============================================================================
const i18nApi = {
  /** 获取翻译 */
  getTranslations(lang) {
    return get('/api/v1/i18n/translations', { lang })
  },
}

// =============================================================================
//  GDPR 合规模块 — /api/gdpr
// =============================================================================
const gdprApi = {
  /** 导出我的数据 */
  exportMyData() {
    return post('/api/v1/gdpr/export')
  },
  /** 删除我的账号 */
  deleteAccount() {
    return post('/api/v1/gdpr/delete-account')
  },
  /** 获取隐私设置 */
  getPrivacySettings() {
    return get('/api/v1/gdpr/privacy-settings')
  },
  /** 更新隐私设置 */
  updatePrivacySettings(data) {
    return put('/api/v1/gdpr/privacy-settings', data)
  },
}

// =============================================================================
//  IM 机器人模块 (bot) — /api/bot
// =============================================================================
const botApi = {
  /** 发送机器人消息 */
  sendMessage(data) {
    return post('/api/v1/bot/send', data)
  },
  /** 获取机器人配置 */
  getConfig() {
    return get('/api/v1/bot/config')
  },
}

// =============================================================================
//  在线学习模块 (learning) — /api/ai/learning
// =============================================================================
const learningApi = {
  /** 获取学习状态 */
  getStatus() {
    return get('/api/v1/ai/learning/status')
  },
  /** 触发学习 */
  triggerLearning() {
    return post('/api/v1/ai/learning/trigger')
  },
}

// =============================================================================
//  盖娅进化大脑 (gaia) — /api/gaia
// =============================================================================
const gaiaApi = {
  /** 获取盖娅状态 */
  getStatus() {
    return get('/api/v1/gaia/status')
  },
  /** 触发盖娅进化 */
  triggerEvolution(data) {
    return post('/api/v1/gaia/evolve', data)
  },
}

// =============================================================================
//  Design QA 模块 — /api/design-qa
// =============================================================================
const designQaApi = {
  /** 提交设计审核 */
  submitReview(data) {
    return post('/api/v1/design-qa/review', data)
  },
  /** 获取审核结果 */
  getReviewResult(taskId) {
    return get(`/api/v1/design-qa/review/${taskId}`)
  },
}

// =============================================================================
//  分析与监控模块 (analytics) — /api/v1/analytics
// =============================================================================
const analyticsApi = {
  /** 获取分析数据 */
  getAnalytics(params) {
    return get('/api/v1/analytics', params)
  },
  /** 获取付款分析 */
  getPaymentAnalytics(params) {
    return get('/api/v1/analytics/payments', params)
  },
}

// =============================================================================
//  Web Vitals 性能监控 — /api/v1/metrics
// =============================================================================
const webVitalsApi = {
  /** 上报 Web Vitals 指标 */
  report(data) {
    return post('/api/v1/metrics/web-vitals', data, { noAuth: true })
  },
}

// =============================================================================
//  分享模块 (share) — /share
// =============================================================================
const shareApi = {
  /** 获取分享二维码 */
  getQRCode(shareToken) {
    return get(`/share/qr/${shareToken}`, {}, { noAuth: true })
  },
  /** 生成 NFC NDEF 记录 */
  getNfcRecord(shareToken) {
    return get(`/share/nfc/${shareToken}`, {}, { noAuth: true })
  },
}

// =============================================================================
//  公开页面 / 健康检查
// =============================================================================
const publicApi = {
  /** 健康检查 */
  health() {
    return get('/api/health', {}, { noAuth: true })
  },
  /** 获取公开 Profile 页面 */
  getPublicProfile(username) {
    return get(`/u/${username}`, {}, { noAuth: true })
  },
}

// =============================================================================
//  上传文件辅助函数
// =============================================================================

/**
 * 上传文件（基于 wx.uploadFile）
 * @param {string} url 上传路径
 * @param {string} filePath 文件路径
 * @param {object} formData 附加表单数据
 * @param {object} options 选项
 * @param {string} options.name 文件字段名（默认 'file'）
 * @param {boolean} options.noAuth 是否不携带 token
 * @returns {Promise}
 */
function uploadFile(url, filePath, formData = {}, options = {}) {
  const app = getApp()
  const token = app.globalData.token
  const baseUrl = getBaseUrl()
  const name = options.name || 'file'

  return new Promise((resolve, reject) => {
    if (!options.noAuth && !token) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      reject(new Error('未登录'))
      return
    }

    const header = {}
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.uploadFile({
      url: `${baseUrl}${url}`,
      filePath,
      name,
      formData,
      header,
      success(res) {
        const { statusCode, data } = res
        try {
          const parsed = typeof data === 'string' ? JSON.parse(data) : data
          if (statusCode >= 200 && statusCode < 300) {
            resolve(parsed)
          } else {
            reject(parsed)
          }
        } catch (e) {
          resolve(data)
        }
      },
      fail(err) {
        reject(err)
      },
    })
  })
}

module.exports = {
  // HTTP 方法（底层）
  get,
  post,
  put,
  del,
  request,
  uploadFile,
  getBaseUrl,

  // 认证
  authApi,

  // 用户
  userApi,

  // 画册/名片
  brochureApi,

  // 标签
  tagApi,

  // 匹配
  matchApi,

  // 访客
  visitorApi,

  // 信任网络
  trustApi,

  // AI 助手
  aiApi,

  // DeepSeek AI 专属
  deepseekApi,

  // 推荐
  recommendApi,

  // 小程序专用
  miniappApi,

  // 支付
  paymentApi,

  // 订阅
  subscriptionApi,

  // 会员
  membershipApi,

  // 消息
  messageApi,

  // 团队
  teamApi,

  // 集成
  integrationApi,

  // 导出
  exportApi,

  // Webhook
  webhookApi,

  // CRM
  crmApi,

  // OAuth/SSO
  oauthApi,

  // API Key
  apiKeyApi,

  // A/B 测试
  abTestApi,

  // 增长分析
  growthApi,

  // App Store
  appStoreApi,

  // 管理后台
  adminApi,

  // 开发者
  developerApi,

  // 发票
  invoiceApi,

  // 知识图谱
  knowledgeGraphApi,

  // 国际化
  i18nApi,

  // GDPR
  gdprApi,

  // 机器人
  botApi,

  // 在线学习
  learningApi,

  // 盖娅进化大脑
  gaiaApi,

  // Design QA
  designQaApi,

  // 分析
  analyticsApi,

  // 性能监控
  webVitalsApi,

  // 分享
  shareApi,

  // 公开接口
  publicApi,

  // AI 配置
  aiConfigApi,

  // 场景
  sceneApi,

  // 人脉网络
  networkApi,

  // 名片编辑
  cardEditApi,
}
