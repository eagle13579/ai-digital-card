const MockService = require('../../../utils/mockService')

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
    report: null,
    loading: true,
    showInviteModal: false,
    inviteUserId: '',
    activeTab: 'members', // members | applications | report
    roleStats: [],
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
      const [platform, membersRes, reportRes, appsRes] = await Promise.all([
        MockService.getPlatformDetail(this.data.platformId),
        MockService.getPlatformMembers(this.data.platformId),
        MockService.getPlatformReport(this.data.platformId),
        MockService.getPlatformApplications(this.data.platformId),
      ])

      const members = membersRes.data || []
      const applications = appsRes.data || []
      const report = reportRes.data

      // 构建角色统计数据
      const roleStats = []
      if (report?.roleDistribution) {
        for (const [role, count] of Object.entries(report.roleDistribution)) {
          const info = ROLE_MAP[role] || { label: role, color: '#999', icon: '❓' }
          roleStats.push({ role, count, ...info })
        }
      }

      this.setData({
        platform,
        members,
        applications,
        report,
        roleStats,
        loading: false,
      })
    } catch (err) {
      console.error('[PlatformManage] 加载数据失败:', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ activeTab: tab })
  },

  goBack() {
    wx.navigateBack()
  },

  goToEdit() {
    wx.navigateTo({
      url: `/pages/platform/create/index?edit=${this.data.platformId}`,
    })
  },

  // ====== 邀请成员 ======
  openInviteModal() {
    this.setData({
      showInviteModal: true,
      inviteUserId: '',
    })
  },

  closeInviteModal() {
    this.setData({ showInviteModal: false })
  },

  onInviteInput(e) {
    this.setData({ inviteUserId: e.detail.value })
  },

  async confirmInvite() {
    const userId = this.data.inviteUserId.trim()
    if (!userId) {
      return wx.showToast({ title: '请输入用户ID', icon: 'none' })
    }

    wx.showLoading({ title: '邀请中...' })
    try {
      await MockService.inviteMember(this.data.platformId, userId)
      wx.hideLoading()
      wx.showToast({ title: '邀请成功', icon: 'success' })
      this.closeInviteModal()
      this.loadData()
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: '邀请失败', icon: 'none' })
    }
  },

  // ====== 审核申请 ======
  async reviewApplication(e) {
    const { id, approved } = e.currentTarget.dataset
    const action = approved === 'true' ? '通过' : '拒绝'
    wx.showLoading({ title: `${action}中...` })
    try {
      await MockService.reviewApplication(id, approved === 'true')
      wx.hideLoading()
      wx.showToast({ title: `已${action}申请`, icon: 'success' })
      this.loadData()
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  // ====== 格式化时间 ======
  formatTime(ts) {
    if (!ts) return ''
    const date = new Date(ts)
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    return `${month}-${day}`
  },

  getRoleInfo(role) {
    return ROLE_MAP[role] || { label: role, color: '#999', icon: '❓' }
  },
})
