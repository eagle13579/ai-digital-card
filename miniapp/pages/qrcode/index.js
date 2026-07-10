/**
 * 我的二维码页面
 * 展示个人名片二维码，支持保存和分享
 */
const { MockService } = require('../../utils/mockService')
const { miniappApi } = require('../../utils/api')

Page({
  data: {
    qrcodeUrl: '',
    userName: '',
    userCompany: '',
    userTitle: '',
    userAvatar: '',
    loading: true,
  },

  onLoad() {
    this.loadData()
  },

  async loadData() {
    try {
      // 并行加载用户信息和二维码
      const [profile, brochures] = await Promise.all([
        MockService.getUserProfile(),
        MockService.getBrochures(),
      ])

      const profileData = profile.data !== undefined ? profile.data : profile
      const userInfo = profileData.userInfo || profileData || {}

      const userName = userInfo.name || ''
      const userCompany = userInfo.company || ''
      const userTitle = userInfo.title || ''
      const userAvatar = userInfo.avatar || ''

      this.setData({
        userName,
        userCompany,
        userTitle,
        userAvatar,
      })

      // 获取第一个名片的分享token来生成二维码
      let brochureList = []
      if (Array.isArray(brochures)) {
        brochureList = brochures
      } else if (brochures.data && Array.isArray(brochures.data)) {
        brochureList = brochures.data
      }

      if (brochureList.length > 0) {
        const shareToken = brochureList[0].share_token || brochureList[0].id
        // 优先用真实API获取二维码，失败用mock
        this.loadQRCode(shareToken)
      } else {
        this.setData({ loading: false })
      }
    } catch (err) {
      console.error('[二维码] 加载失败:', err)
      this.setData({ loading: false })
    }
  },

  loadQRCode(shareToken) {
    // 尝试从API获取
    wx.request({
      url: `${getApp().globalData.baseUrl || 'https://api.liankebao.top'}/api/v1/business-card/cards/qrcode`,
      method: 'GET',
      data: { share_token: shareToken, width: 280 },
      success: (res) => {
        if (res.statusCode === 200 && res.data?.qrcode_url) {
          this.setData({ qrcodeUrl: res.data.qrcode_url, loading: false })
        } else {
          this.fallbackQRCode(shareToken)
        }
      },
      fail: () => this.fallbackQRCode(shareToken),
    })
  },

  fallbackQRCode(shareToken) {
    // Mock生成二维码：用小程序码API或预设图片
    const pages = getCurrentPages()
    // 使用二维码API服务
    const baseUrl = 'https://api.liankebao.top'
    this.setData({
      qrcodeUrl: `${baseUrl}/api/v1/business-card/cards/qrcode?share_token=${shareToken}&width=280`,
      loading: false,
    })
  },

  saveQRCode() {
    wx.showToast({ title: '长按图片即可保存', icon: 'none', duration: 2000 })
  },

  shareCard() {
    wx.showShareMenu({ withShareTicket: true })
  },

  onShareAppMessage() {
    return {
      title: `${this.data.userName || '我'}的AI数智名片`,
      path: `/pages/card/card`,
    }
  },
})
