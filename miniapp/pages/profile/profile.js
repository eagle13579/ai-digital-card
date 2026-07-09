/**
 * 我的 - 个人中心/会员信息/设置
 */
const { MockService } = require('../../utils/mockService')
const { userApi } = require('../../utils/api')

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
    // 使用额度
    usage: {
      card_count: 0,
      card_limit: 1,
      ocr_count: 0,
      ocr_limit: 3,
    },
    isPro: false,
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
        MockService.getUserProfile(),
        MockService.getBrochures(),
        MockService.getTrustNetwork(),
        MockService.getVisitorStats(),
      ])

      const profileData = profile.data !== undefined ? profile.data : profile
      const memberLevel = profileData.memberLevel || profileData.member_level || 'free'
      const memberLevelText = { free: 'Free', gold: 'Gold', diamond: 'Diamond', board: 'Board' }[memberLevel] || 'Free'
      const isPro = memberLevel !== 'free'

      const usage = {
        card_count: 1,
        card_limit: memberLevel === 'free' ? 1 : 10,
        ocr_count: 0,
        ocr_limit: memberLevel === 'free' ? 3 : 100,
      }

      const trustData = trustNet.data !== undefined ? trustNet.data : (trustNet || {})
      const trustCount = (trustData.trusting || []).length

      const vStats = visitorStats.data !== undefined ? visitorStats.data : visitorStats
      const stats = {
        visitors: vStats.total_visits || 0,
        matches: 0,
        unlocks: 0,
        views: vStats.view_count || 0,
      }

      const userInfo = {
        id: profileData.id || '',
        name: profileData.name || '',
        avatar: profileData.avatar || '',
        company: profileData.company || '',
        title: profileData.title || '',
      }

      this.setData({
        userInfo,
        memberLevel,
        memberLevelText,
        memberExpire: '',
        trustCount,
        newVisitorCount: 0,
        stats,
        usage,
        isPro,
        loading: false,
      })

      const app = getApp()
      if (typeof app.updateUserInfo === 'function') app.updateUserInfo(userInfo)
      if (typeof app.updateMemberLevel === 'function') app.updateMemberLevel(memberLevel)
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
    wx.navigateTo({ url: '/pages/membership/membership' })
  },

  // 访客记录 → AI数据洞察
  goVisitorLog() {
    wx.navigateTo({ url: '/pages/ai/insight/index' })
  },

  // 信任网络 → 人脉图谱
  goTrustNetwork() {
    wx.navigateTo({ url: '/pages/network/graph/index' })
  },

  // 隐私设置
  goPrivacy() {
    wx.navigateTo({ url: '/pages/agreement/privacy/privacy' })
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
          wx.reLaunch({ url: '/pages/login/index' })
        }
      },
    })
  },

  // 跳转修改资料页面
  goEditProfile() {
    wx.showModal({
      title: '提示',
      content: '资料编辑功能即将开放，敬请期待',
      showCancel: false
    })
  },

  // 保存资料（API调用）
  async saveProfile(data) {
    try {
      const res = await userApi.updateProfile(data)
      wx.showToast({ title: '保存成功', icon: 'success' })
      this.loadProfile()
      return res
    } catch (err) {
      console.error('保存资料失败:', err)
      wx.showToast({ title: '保存失败', icon: 'none' })
      throw err
    }
  },
})
