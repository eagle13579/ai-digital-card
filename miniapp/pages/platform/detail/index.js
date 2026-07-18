const { getPlatform, getMembers, getResourceUnits, getOpportunities, joinPlatform } = require('../../../utils/platform-bridge')
const { connectionApi } = require('../../../utils/api')
const store = require('../../../utils/store')

Page({
  data: {
    platformId: '',
    platform: null,
    loading: true,
    activeTab: 'info',
    isCreator: false,
    alreadyJoined: false,
    joining: false,
    showContactModal: false,
    showInviteModal: false,
    resourceUnits: [],
    opportunities: [],
    useRealApi: true,
    // 邀请表单
    invitePhone: '',
    inviteName: '',
    inviting: false,
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

  async loadData() {
    this.setData({ loading: true })
    const { platformId, useRealApi } = this.data
    try {
      const [platformRes, membersRes, unitsRes, oppsRes] = await Promise.all([
        getPlatform(platformId, useRealApi),
        getMembers(platformId, useRealApi),
        getResourceUnits(platformId, useRealApi),
        getOpportunities(platformId, useRealApi),
      ])

      const platform = platformRes.data || platformRes
      if (!platform) {
        wx.showToast({ title: '平台不存在', icon: 'none' })
        wx.navigateBack()
        return
      }

      const { userInfo } = store.getState()
      const userId = userInfo?.id || ''
      const isCreator = platform.creator_id === userId

      let alreadyJoined = false
      try {
        const members = membersRes.data || []
        alreadyJoined = members.some(m => m.id === userId)
      } catch (e) {
        console.warn('[PlatformDetail] 获取成员列表失败', e)
      }

      this.setData({
        platform,
        isCreator,
        alreadyJoined,
        resourceUnits: unitsRes.data || [],
        opportunities: oppsRes.data || [],
        loading: false,
      })
    } catch (err) {
      console.error('[PlatformDetail] 加载数据失败:', err)
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

  openContactModal() {
    this.setData({ showContactModal: true })
  },

  closeContactModal() {
    this.setData({ showContactModal: false })
  },

  openInviteModal() {
    this.setData({ showInviteModal: true, invitePhone: '', inviteName: '' })
  },

  closeInviteModal() {
    this.setData({ showInviteModal: false })
  },

  stopPropagation() {},

  makeCall() {
    const phone = this.data.platform?.phone || '13800138000'
    wx.makePhoneCall({ phoneNumber: phone })
  },

  /** 邀请询赋好友 — 通过手机号发送连接请求 */
  async inviteFromApp() {
    const { inviteName, invitePhone, platformId, inviting } = this.data
    if (inviting) return

    if (!inviteName.trim() && !invitePhone.trim()) {
      // 如果没有已填写的信息，展示输入框让用户输入
      wx.showModal({
        title: '邀请好友加入平台',
        content: '请输入好友的手机号或姓名',
        editable: true,
        placeholderText: '手机号或姓名',
        success: async (res) => {
          if (res.confirm && res.content.trim()) {
            this.setData({ inviting: true })
            wx.showLoading({ title: '发送邀请...' })
            try {
              await connectionApi.request(platformId, `邀请加入平台: ${platformId}`, 'platform')
              wx.hideLoading()
              wx.showToast({ title: '邀请已发送', icon: 'success' })
              this.closeInviteModal()
            } catch (err) {
              wx.hideLoading()
              wx.showToast({ title: err.message || '邀请失败', icon: 'none' })
            } finally {
              this.setData({ inviting: false })
            }
          }
        },
      })
      return
    }

    this.setData({ inviting: true })
    wx.showLoading({ title: '发送邀请...' })
    try {
      await connectionApi.request(platformId, `邀请加入平台: ${inviteName || invitePhone}`, 'platform')
      wx.hideLoading()
      wx.showToast({ title: '邀请已发送', icon: 'success' })
      this.closeInviteModal()
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: err.message || '邀请失败', icon: 'none' })
    } finally {
      this.setData({ inviting: false })
    }
  },

  /** 从微信邀请 — 分享给微信好友 */
  inviteFromWechat() {
    this.closeInviteModal()
    // 使用微信原生分享
    wx.shareAppMessage?.({
      title: `邀请你加入 ${this.data.platform?.name || '资源平台'}`,
      path: `/pages/platform/detail/index?id=${this.data.platformId}`,
    })
  },

  /** 展示平台二维码 */
  showQRCode() {
    this.closeInviteModal()
    wx.showToast({ title: '展示平台二维码', icon: 'none' })
  },

  /** 加入平台（当前用户） */
  async handleJoin() {
    if (this.data.joining) return

    const { isLoggedIn } = store.getState()
    if (!isLoggedIn) {
      wx.navigateTo({ url: '/pages/login/index' })
      return
    }

    this.setData({ joining: true })
    wx.showLoading({ title: '加入中...' })

    try {
      const result = await joinPlatform(this.data.platformId, this.data.useRealApi)
      wx.hideLoading()
      wx.showToast({ title: result.data?.message || '加入成功', icon: 'success' })
      this.setData({
        alreadyJoined: true,
        joining: false,
      })
      this.loadData()
    } catch (err) {
      wx.hideLoading()
      console.error('[PlatformDetail] 加入失败:', err)
      wx.showToast({ title: '加入失败，请重试', icon: 'none' })
      this.setData({ joining: false })
    }
  },

  /** 输入邀请姓名 */
  onInviteNameInput(e) {
    this.setData({ inviteName: e.detail.value })
  },

  /** 输入邀请手机号 */
  onInvitePhoneInput(e) {
    this.setData({ invitePhone: e.detail.value })
  },
})
