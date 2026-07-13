/**
 * 统一数据服务层
 * 支持Mock/真实API切换
 * 
 * 快速切换方法：
 *   1. 将 USE_MOCK 改为 false 即可使用真实API
 *   2. 将 USE_MOCK 改为 true 即可使用Mock数据
 * 
 * 架构说明：
 *   - Mock数据逻辑已拆分至 mockData.js
 *   - 本文件只保留真实API调用 + USE_MOCK开关委托
 *   - 拆分日期: 2026-07-13
 */
const store = require('./store')
const { Logger } = require('./util')
const { get, post, put, del } = require('./request')
const { userApi, brochureApi, authApi, miniappApi, matchApi, tagApi, visitorApi, trustApi, aiApi, sixDegreesApi, organizationApi } = require('./api')
const { MockData } = require('./mockData')

const MockService = {
  USE_MOCK: false,

  // ===== 用户/认证 =====

  async getProfile() {
    return this.getUserProfile()
  },

  async getUserProfile() {
    if (this.USE_MOCK) return MockData.getUserProfile()
    return userApi.getProfile()
  },

  async login(data) {
    if (this.USE_MOCK) return MockData.login(data)
    return authApi.login(data)
  },

  async wxMiniLogin(data) {
    if (this.USE_MOCK) return MockData.wxMiniLogin(data)
    return authApi.wxMiniLogin(data.code)
  },

  // ===== 名片（Brochure） =====

  async getBrochures() {
    if (this.USE_MOCK) return MockData.getBrochures()
    return brochureApi.list()
  },

  async getBrochureById(id) {
    if (this.USE_MOCK) return MockData.getBrochureById(id)
    return brochureApi.get(id)
  },

  async createBrochure(data) {
    if (this.USE_MOCK) return MockData.createBrochure(data)
    return brochureApi.create(data)
  },

  async deleteBrochure(id) {
    if (this.USE_MOCK) return MockData.deleteBrochure(id)
    return brochureApi.delete(id)
  },

  // ===== 匹配推荐 =====

  async getRecommendList(page = 1, size = 20) {
    if (this.USE_MOCK) return MockData.getRecommendList(page, size)
    return matchApi.getRecommendList(page, size)
  },

  async getMatchDetail(id) {
    if (this.USE_MOCK) return MockData.getMatchDetail(id)
    return matchApi.getMatchDetail(id)
  },

  // ===== 标签 =====

  async getTags() {
    if (this.USE_MOCK) return MockData.getTags()
    return tagApi.list()
  },

  // ===== 访客统计 =====

  async getVisitorStats() {
    if (this.USE_MOCK) return MockData.getVisitorStats()
    return visitorApi.getStats()
  },

  // ===== 信任网络 =====

  async getTrustNetwork() {
    if (this.USE_MOCK) return MockData.getTrustNetwork()
    return trustApi.getNetwork()
  },

  // ===== AI 智能 =====

  async aiChat(question) {
    if (this.USE_MOCK) return MockData.aiChat(question)
    return aiApi.write({ prompt: question })
  },

  async aiGenerate(type, input) {
    if (this.USE_MOCK) return MockData.aiGenerate(type, input)
    return aiApi.generate({ type, input })
  },

  // ===== 资源平台 =====

  async createResource(formData) {
    if (this.USE_MOCK) return MockData.createResource(formData)
    return post('/api/v1/resources', formData)
  },

  // ===== 好友列表 =====

  async getFriendsList(userId) {
    if (this.USE_MOCK) return MockData.getFriendsList(userId)
    return trustApi.getNetwork(userId)
  },

  // ===== BFS触达路径 =====

  async findPath(targetUserId) {
    if (this.USE_MOCK) return MockData.findPath(targetUserId)
    return trustApi.getScore(targetUserId)
  },

  // ===== 平台管理 =====

  async createPlatform(formData) {
    if (this.USE_MOCK) return MockData.createPlatform(formData)
    return post('/api/v1/platforms', formData)
  },

  async getPlatformList() {
    if (this.USE_MOCK) return MockData.getPlatformList()
    return get('/api/v1/platforms')
  },

  async getPlatformDetail(platformId) {
    if (this.USE_MOCK) return MockData.getPlatformDetail(platformId)
    return get(`/api/v1/platforms/${platformId}`)
  },

  async getPlatformMembers(platformId) {
    if (this.USE_MOCK) return MockData.getPlatformMembers(platformId)
    return get(`/api/v1/platforms/${platformId}/members`)
  },

  async getPlatformApplications(platformId) {
    if (this.USE_MOCK) return MockData.getPlatformApplications(platformId)
    return get(`/api/v1/platforms/${platformId}/applications`)
  },

  async reviewApplication(applicationId, approved) {
    if (this.USE_MOCK) return MockData.reviewApplication(applicationId, approved)
    return put(`/api/v1/applications/${applicationId}`, { approved })
  },

  async inviteMember(platformId, userId) {
    if (this.USE_MOCK) return MockData.inviteMember(platformId, userId)
    return post(`/api/v1/platforms/${platformId}/invite`, { user_id: userId })
  },

  async getPlatformReport(platformId) {
    if (this.USE_MOCK) return MockData.getPlatformReport(platformId)
    return get(`/api/v1/platforms/${platformId}/report`)
  },

  async getResourceCoverage(platformId) {
    if (this.USE_MOCK) return MockData.getResourceCoverage(platformId)
    return get(`/api/v1/platforms/${platformId}/coverage`)
  },

  async getResourceRanking(platformId) {
    if (this.USE_MOCK) return MockData.getResourceRanking(platformId)
    return get(`/api/v1/platforms/${platformId}/ranking`)
  },

  async getResourceUnits(platformId) {
    if (this.USE_MOCK) return MockData.getResourceUnits(platformId)
    return get(`/api/v1/platforms/${platformId}/resource-units`)
  },

  async getPlatformOpportunities(platformId) {
    if (this.USE_MOCK) return MockData.getPlatformOpportunities(platformId)
    return get(`/api/v1/platforms/${platformId}/opportunities`)
  },

  async joinPlatform(platformId) {
    if (this.USE_MOCK) return MockData.joinPlatform(platformId)
    return post(`/api/v1/platforms/${platformId}/join`)
  },

  // ===== 洞察数据 =====

  async getInsightData() {
    if (this.USE_MOCK) return MockData.getInsightData()
    return aiApi.insight()
  },

  // ===== 六度人脉 =====

  async getSixDegreesNetwork(userId, maxDepth = 3) {
    if (this.USE_MOCK) return MockData.getSixDegreesNetwork(userId, maxDepth)
    return sixDegreesApi.network(userId, maxDepth)
  },

  async getSixDegreesPath(fromId, toId, maxDepth = 6) {
    if (this.USE_MOCK) return MockData.getSixDegreesPath(fromId, toId, maxDepth)
    return sixDegreesApi.path(fromId, toId, maxDepth)
  },

  async getSixDegreesRelations(userId) {
    if (this.USE_MOCK) return MockData.getSixDegreesRelations(userId)
    return sixDegreesApi.relations(userId)
  },

  async createSixDegreesRelation(data) {
    if (this.USE_MOCK) return MockData.createSixDegreesRelation(data)
    return sixDegreesApi.createRelation(data)
  },

  async updateSixDegreesTrust(id, data) {
    if (this.USE_MOCK) return MockData.updateSixDegreesTrust(id, data)
    return sixDegreesApi.updateTrust(id, data)
  },

  // ===== 组织管理 =====

  async getOrganizationList() {
    if (this.USE_MOCK) return MockData.getOrganizationList()
    return organizationApi.list()
  },

  async getOrganizationDetail(orgId) {
    if (this.USE_MOCK) return MockData.getOrganizationDetail(orgId)
    return organizationApi.get(orgId)
  },

  async getOrganizationMembers(orgId) {
    if (this.USE_MOCK) return MockData.getOrganizationMembers(orgId)
    return organizationApi.members(orgId)
  },
}

module.exports = { MockService }
