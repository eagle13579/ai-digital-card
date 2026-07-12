const { MockService } = require('../../../utils/mockService')
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
    try {
      const [platform, membersRes, appsRes, coverageRes, rankingRes] = await Promise.all([
        MockService.getPlatformDetail(this.data.platformId),
        MockService.getPlatformMembers(this.data.platformId),
        MockService.getPlatformApplications(this.data.platformId),
        MockService.getResourceCoverage(this.data.platformId),
        MockService.getResourceRanking(this.data.platformId),
      ])

      const members = membersRes.data || []
      const applications = appsRes.data || []
      const coverage = coverageRes.data || {}
      const ranking = rankingRes.data || []

      const pendingApplications = applications.filter(a => a.status === 'pending').length
      const pendingConnections = Math.floor(Math.random() * 5)

      this.setData({
        platform,
        members,
        applications,
        coverage,
        ranking: ranking.slice(0, 3),
        linkableCount: coverage.linkableCities || 1,
        pendingApplications,
        pendingConnections,
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

  goToMemberManage() {
    const platformId = this.data.platformId
    if (platformId) {
      wx.navigateTo({ url: `/pages/platform/detail/index?id=${platformId}` })
    }
  },

  handleImportMembers() {
    wx.showModal({
      title: '一键导入会员',
      content: '功能即将上线，敬请期待。届时可通过Excel批量导入或从询赋App中直接邀请会员加入平台。',
      showCancel: false,
      confirmText: '知道了',
    })
  },

  goToMessage() {
    wx.showModal({
      title: '消息发布/管理',
      content: '功能即将上线，敬请期待。届时可向平台成员群发通知、活动邀请及行业资讯。',
      showCancel: false,
      confirmText: '知道了',
    })
  },

  goToNewMemberReview() {
    const platformId = this.data.platformId
    if (platformId) {
      wx.navigateTo({ url: `/pages/platform/detail/index?id=${platformId}` })
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