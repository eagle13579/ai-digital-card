/**
 * 我的 - 个人中心/会员信息/设置
 */
const { MockService } = require('../../utils/mockService')

Page({
  data: {
    loading: true,
    userInfo: {},
    memberLevel: 'free',
    memberLevelText: 'Free',
    memberExpire: '',
    trustCount: 0,
    newVisitorCount: 0,
    stats: { visitors: 0, matches: 0, unlocks: 0, views: 0 },
  },

  onLoad() {
    this.loadProfile()
  },

  onShow() {
    if (!this.data.loading) {
      this.loadProfile()
    }
  },

  async loadProfile() {
    this.setData({ loading: true })
    try {
      const [profile, brochures, trustNet, visitorStats] = await Promise.all([
        MockService.getProfile(),
        MockService.getBrochures(),
        MockService.getTrustNetwork(),
        MockService.getVisitorStats(),
      ])

      const brochureList = Array.isArray(brochures) ? brochures : (brochures.data || [])
      const brochure = brochureList[0]

      const memberLevel = profile.member_level || 'free'
      const memberLevelText = { free: 'Free', gold: 'Gold', diamond: 'Diamond', board: 'Board' }[memberLevel] || 'Free'

      let stats = { visitors: visitorStats.total_visits || 0, matches: 0, unlocks: 0, views: visitorStats.view_count || 0 }

      const trustCount = (trustNet.trusting || []).length

      this.setData({
        userInfo: {
          id: profile.id,
          name: profile.name || '',
          avatar: profile.avatar || '',
          company: profile.company || '',
          title: profile.title || '',
        },
        memberLevel,
        memberLevelText,
        memberExpire: profile.member_expire || '',
        trustCount,
        stats,
        loading: false,
      })

      const app = getApp()
      app.updateUserInfo(this.data.userInfo)
      app.updateMemberLevel(memberLevel)
    } catch (err) {
      console.error('加载个人数据失败:', err)
      this.setData({ loading: false })
    }
  },

  // 编辑名片
  goEditCard() {
    wx.navigateTo({ url: '/pages/brochure/create/index' })
  },

  // 画册管理
  goAlbum() {
    wx.navigateTo({ url: '/pages/brochure/create/index' })
  },

  // 会员中心
  goMember() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  // 访客记录
  goVisitorLog() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  // 信任网络
  goTrustNetwork() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  // 隐私设置
  goPrivacy() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  // 关于
  goAbout() {
    wx.showToast({ title: 'AI数智名片 v1.0.0', icon: 'none' })
  },

  // 退出登录
  logout() {
    wx.showModal({
      title: '确认退出',
      content: '退出后需要重新登录',
      success: (res) => {
        if (res.confirm) {
          const app = getApp()
          app.clearLogin()
          wx.reLaunch({ url: '/pages/index/index' })
        }
      },
    })
  },
})
