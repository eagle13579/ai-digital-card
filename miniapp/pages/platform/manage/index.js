const { getPlatform, getMembers, getApplications, getCoverage, getRanking } = require('../../../utils/platform-bridge')
const { connectionApi } = require('../../../utils/api')

const ROLE_MAP = {
  secretary_general: { label: '秘书长', color: '#8b5cf6', icon: '👑' },
  secretariat: { label: '秘书处', color: '#06b6d4', icon: '⚙️' },
  member: { label: '会员', color: '#22c55e', icon: '👤' },
}

Page({
  data: {
    platformId: '',
    platform: null,
    members: [],
    applications: [],
    coverage: {},
    ranking: [],
    loading: true,
    showInviteModal: false,
    linkableCount: 1,
    pendingApplications: 0,
    pendingConnections: 0,
    useRealApi: true,
  },

  onLoad(options) {
    const platformId = options.id
    if (!platformId) {
      wx.showToast({ title: '参数错误', icon: 'none' })
      return
    }
    this.setData({ platformId })
    this.loadData()
  },

  onShow() {
    if (this.data.platformId) {
      this.loadData()
    }
  },

  async loadData() {
    this.setData({ loading: true })
    const { platformId, useRealApi } = this.data
    try {
      const [platform, membersRes, appsRes, coverageRes, rankingRes, pendingRes] = await Promise.all([
        getPlatform(platformId, useRealApi),
        getMembers(platformId, useRealApi),
        getApplications(platformId, useRealApi),
        getCoverage(platformId, useRealApi),
        getRanking(platformId, useRealApi),
        // 从API获取真实的待审核建联数
        connectionApi.listPending().catch(() => []),
      ])

      const members = membersRes.data || []
      const applications = appsRes.data || []
      const coverage = coverageRes.data || {}
      const ranking = rankingRes.data || []
      const pendingConnectionsCount = Array.isArray(pendingRes) ? pendingRes.length : (pendingRes?.length || 0)

      const pendingApplications = applications.filter(a => a.status === 'pending').length

      this.setData({
        platform: platform.data || platform,
        members,
        applications,
        coverage,
        ranking: ranking.slice(0, 3),
        linkableCount: coverage.linkableCities || 1,
        pendingApplications,
        pendingConnections: pendingConnectionsCount,
        loading: false,
      })
    } catch (err) {
      console.error('[PlatformManage] 加载数据失败:', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  goBack() {
    wx.navigateBack()
  },

  openInviteModal() {
    this.setData({ showInviteModal: true })
  },

  closeInviteModal() {
    this.setData({ showInviteModal: false })
  },

  stopPropagation() {},

  inviteFromApp() {
    wx.showToast({ title: '选择询赋好友邀请', icon: 'none' })
    this.closeInviteModal()
  },

  inviteFromWechat() {
    wx.showToast({ title: '选择微信好友邀请', icon: 'none' })
    this.closeInviteModal()
  },

  showQRCode() {
    wx.showToast({ title: '展示平台二维码', icon: 'none' })
    this.closeInviteModal()
  },

  /** 跳转成员管理 — 修复：改为跳转到 team/manage（真正的成员管理页） */
  goToMemberManage() {
    const platformId = this.data.platformId
    if (platformId) {
      wx.navigateTo({ url: `/pages/team/manage/index?platformId=${platformId}` })
    }
  },

  handleImportMembers() {
    const platformId = this.data.platformId
    if (platformId) {
      wx.navigateTo({ url: `/pages/platform/import/index?id=${platformId}` })
    }
  },

  goToMessage() {
    const platformId = this.data.platformId
    if (platformId) {
      wx.navigateTo({ url: `/pages/platform/message/index?id=${platformId}` })
    }
  },

  /** 跳转新人审核 — 修复：改为跳转到 platform/review（真正的审核页） */
  goToNewMemberReview() {
    const platformId = this.data.platformId
    if (platformId) {
      wx.navigateTo({ url: `/pages/platform/review/index?id=${platformId}` })
    }
  },

  async goToConnectionReview() {
    const platformId = this.data.platformId
    try {
      const pending = await connectionApi.listPending()
      if (pending && pending.length > 0) {
        wx.navigateTo({ url: `/pages/network/graph/index` })
      } else {
        wx.showToast({ title: '暂无待审核的建联请求', icon: 'none' })
      }
    } catch (err) {
      console.warn('[PlatformManage] 查询建联请求失败:', err)
      wx.navigateTo({ url: `/pages/network/graph/index` })
    }
  },

  getRoleInfo(role) {
    return ROLE_MAP[role] || { label: role, color: '#999', icon: '❓' }
  },

  getRankColor(rank) {
    const colors = ['#fbbf24', '#9ca3af', '#f97316']
    return colors[rank - 1] || '#9ca3af'
  },
})
