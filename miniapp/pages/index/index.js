/**
 * 首页 - 名片列表 + 推荐
 * 使用MockService获取数据
 */
const { MockService } = require('../../utils/mockService')
const { Logger } = require('../../utils/util')

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

    // 平台推荐
    platformRecommend: [
      { id: 1, name: 'AI技术合作平台', desc: 'AI技术开发·模型训练·数据标注', icon: '🤖', bg: 'linear-gradient(135deg, #667eea, #764ba2)' },
      { id: 2, name: '供应链资源平台', desc: '供应商对接·物流配送·仓储服务', icon: '🚚', bg: 'linear-gradient(135deg, #f093fb, #f5576c)' },
      { id: 3, name: '投融资对接平台', desc: '天使投资·VC融资·并购重组', icon: '💰', bg: 'linear-gradient(135deg, #4facfe, #00f2fe)' },
      { id: 4, name: '市场营销平台', desc: '品牌推广·渠道拓展·流量获客', icon: '📢', bg: 'linear-gradient(135deg, #43e97b, #38f9d7)' },
    ],
  },

  onLoad(options) {
    Logger.info('首页', '页面加载')
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
      const [profile, brochures, trustNet, recommend] = await Promise.all([
        MockService.getUserProfile().catch(() => ({ userInfo: {}, memberLevel: 'free' })),
        MockService.getBrochures().catch(() => []),
        MockService.getTrustNetwork().catch(() => ({ trusting: [], trusted_by: [] })),
        MockService.getRecommendList().catch(() => []),
      ])

      const userInfoData = profile.userInfo || profile
      const brochuresList = brochures
      const trustData = trustNet
      const recommendData = recommend

      const brochure = Array.isArray(brochuresList) ? brochuresList[0] : null

      const trustList = trustData.trusting || []
      const trustCount = trustList.length

      let stats = { visitors: 0, matches: recommendData.length, trust: trustCount }
      if (brochure) {
        const vStats = await MockService.getVisitorStats().catch(() => null)
        if (vStats) {
          stats.visitors = vStats.total_visits || vStats.total || 0
        }
      }

      const userInfo = {
        name: userInfoData.name || '',
        avatar: userInfoData.avatar || '',
        company: userInfoData.company || '',
        title: userInfoData.title || '',
      }

      const memberLevel = profile.memberLevel || 'free'
      const memberLevelText = { free: 'Free', gold: 'Gold', diamond: 'Diamond', board: 'Board' }[memberLevel] || 'Free'

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
          viewCount: brochure.view_count || brochure.viewCount || 0,
          pageCount: brochure.pages_count || brochure.pageCount || 0,
        } : null,
        trustCount,
        trustList: trustList.slice(0, 10),
        recommendList: Array.isArray(recommendData) ? recommendData.slice(0, 3) : [],
        visitorList: [],
        loading: false,
      })

      Logger.info('首页', '数据加载完成')
    } catch (err) {
      Logger.error('首页', '加载失败', err)
      this.setData({ loading: false })
    }
  },

  goEditCard() {
    wx.navigateTo({ url: '/pages/brochure/create/index' })
  },

  goPreview() {
    const brochure = this.data.brochure
    if (brochure) {
      wx.navigateTo({ url: `/pages/brochure/preview/index?id=${brochure.id}` })
    } else {
      wx.navigateTo({ url: '/pages/brochure/create/index' })
    }
  },

  goQrCode() {
    wx.navigateTo({ url: '/pages/qrcode/index' })
  },

  shareCard() {
    wx.showShareMenu({ withShareTicket: true })
  },

  goTrust() {
    wx.navigateTo({ url: '/pages/network/graph/index' })
  },

  goMatch() {
    wx.navigateTo({ url: '/pages/ai/match/index' })
  },

  goMatchDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/ai/match/index?id=${id}` })
  },

  // 创建资源平台
  goCreatePlatform() {
    wx.navigateTo({ url: '/pages/platform/create/index' })
  },

  // 平台推荐详情
  goPlatformDetail(e) {
    const name = e.currentTarget.dataset.url || e.currentTarget.dataset.item
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  onShareAppMessage() {
    const brochure = this.data.brochure
    return {
      title: this.data.userInfo.name + '的AI数智名片',
      path: brochure ? `/pages/brochure/preview/index?id=${brochure.id}` : '/pages/index/index',
    }
  },
})