const { MockService } = require('../../../utils/mockService')
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
    try {
      const [platform, membersRes, unitsRes, oppsRes] = await Promise.all([
        MockService.getPlatformDetail(this.data.platformId),
        MockService.getPlatformMembers(this.data.platformId),
        MockService.getResourceUnits(this.data.platformId),
        MockService.getPlatformOpportunities(this.data.platformId),
      ])
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
    this.setData({ showInviteModal: true })
  },

  closeInviteModal() {
    this.setData({ showInviteModal: false })
  },

  stopPropagation() {},

  makeCall() {
    const phone = this.data.platform?.phone || '13800138000'
    wx.makePhoneCall({ phoneNumber: phone })
  },

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
      const result = await MockService.joinPlatform(this.data.platformId)
      wx.hideLoading()
      wx.showToast({ title: result.message, icon: 'success' })
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
})