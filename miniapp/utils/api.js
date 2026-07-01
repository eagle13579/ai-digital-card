/**
 * API 接口封装
 * 指向新后端 http://localhost:8003
 */
const { get, post, put, del } = require('./request')

// ===== 小程序专用模块 (mini app) =====
const miniappApi = {
  login(data) {
    return post('/api/v1/miniapp/login', data, { noAuth: true })
  },
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

// ===== 认证模块 =====
const authApi = {
  login(data) {
    return post('/api/auth/login', data, { noAuth: true })
  },
  register(data) {
    return post('/api/auth/register', data, { noAuth: true })
  },
  logout() {
    return post('/api/auth/logout')
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
}

// ===== 画册(名片)模块 =====
const brochureApi = {
  list(params) {
    return get('/api/brochures', params)
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
  unlock(matchId) {
    return post(`/api/match/${matchId}/unlock`)
  },
}

// ===== 信任模块 =====
const trustApi = {
  getNetwork() {
    return get('/api/trust/network')
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

module.exports = {
  miniappApi,
  authApi,
  userApi,
  brochureApi,
  tagApi,
  matchApi,
  trustApi,
  visitorApi,
}
