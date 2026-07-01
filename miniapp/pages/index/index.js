/**
 * 首页 - 名片列表 + 推荐
 * API调用指向 http://localhost:8003/api/v1/miniapp/
 */
const { userApi, brochureApi, matchApi, trustApi, visitorApi } = require('../../utils/api')
const { formatRelativeTime } = require('../../utils/util')

Page({
  data: {
    loading: true,
    userInfo: {},
    memberLevel: 'free',
    memberLevelText: 'Free',
    stats: { visitors: 0, matches: 0, trust: 0 },
    brochure: null,
    trustCount: 0,
    trustList: [],
    recommendList: [],
    visitorList: [],
  },

  onLoad(options) {
    this.loadPageData()
  },

  onShow() {
    const app = getApp()
    if (app.globalData.token && !this.data.loading) {
      this.loadPageData()
    }
  },

  async loadPageData() {
    this.setData({ loading: true })
    try {
      // 并行加载数据
      const [profile, brochures, trustNet, recommend] = await Promise.all([
        userApi.getProfile().catch(() => null),
        brochureApi.list().catch(() => ({ data: [] })),
        trustApi.getNetwork().catch(() => ({ trusting: [], trusted_by: [] })),
        matchApi.getRecommend({ limit: 3 }).catch(() => []),
      ])

      const brochuresList = brochures.data || brochures
      const brochure = Array.isArray(brochuresList) ? brochuresList[0] : null

      const trustList = trustNet.trusting || []
      const trustCount = trustList.length

      // 如果已有画册，获取访客统计
      let stats = { visitors: 0, matches: 0, trust: trustCount }
      if (brochure) {
        const vStats = await visitorApi.getStats(brochure.id).catch(() => null)
        if (vStats) {
          stats.visitors = vStats.total_visits || 0
        }
      }

      // 构建用户信息
      const userInfo = {
        name: profile?.name || '',
        avatar: profile?.avatar || '',
        company: profile?.company || '',
        title: profile?.title || '',
      }

      const memberLevel = profile?.member_level || 'free'
      const memberLevelText = { free: 'Free', gold: 'Gold', diamond: 'Diamond', board: 'Board' }[memberLevel] || 'Free'

      // 更新全局数据
      const app = getApp()
      app.updateUserInfo(userInfo)
      app.updateMemberLevel(memberLevel)

      this.setData({
        userInfo,
        memberLevel,
        memberLevelText,
        stats,
        brochure: brochure ? {
          id: brochure.id,
          cover: brochure.cover,
          title: brochure.title,
          viewCount: brochure.view_count || 0,
          pageCount: brochure.pages_count || 0,
        } : null,
        trustCount,
        trustList,
        recommendList: Array.isArray(recommend) ? recommend : (recommend.data || []),
        visitorList: [],
        loading: false,
      })
    } catch (err) {
      console.error('首页加载失败:', err)
      this.setData({ loading: false })
    }
  },

  // 跳转编辑名片
  goEditCard() {
    wx.navigateTo({ url: '/pages/my-card/index' })
  },

  // 跳转预览
  goPreview() {
    const brochure = this.data.brochure
    if (brochure) {
      wx.navigateTo({ url: `/pages/preview/index?id=${brochure.id}` })
    } else {
      wx.navigateTo({ url: '/pages/my-card/index' })
    }
  },

  // 二维码
  goQrCode() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  // 分享名片
  shareCard() {
    wx.showShareMenu({ withShareTicket: true })
  },

  // 信任网络
  goTrust() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  // 匹配推荐
  goMatch() {
    wx.switchTab({ url: '/pages/match/index' })
  },

  // 匹配详情
  goMatchDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/match/index?id=${id}` })
  },

  onShareAppMessage() {
    const brochure = this.data.brochure
    return {
      title: this.data.userInfo.name + '的AI数字名片',
      path: brochure ? `/pages/preview/index?id=${brochure.id}` : '/pages/index/index',
    }
  },
})
