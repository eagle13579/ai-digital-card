/**
 * 首页 - 名片列表 + 推荐
 * 使用MockService获取数据
 */
const { MockService } = require('../../utils/mockService')
const store = require('../../utils/store')
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
    showEmpty: false,
    visitorList: [],
    showUpgradeHint: false,

    sceneMode: 'personal',
    sceneModeExpanded: false,
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
    const { isLoggedIn, dataDirty } = store.getState()
    if (isLoggedIn) {
      if (dataDirty || !this.data.loading) {
        store.clearDataDirty()
        this.loadPageData()
      }
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

      const { getLevelText } = require('../../utils/levels')
      const memberLevel = profile.memberLevel || 'free'
      const memberLevelText = getLevelText(memberLevel)

      const store = require('../../utils/store')
      store.updateUserInfo(userInfo)
      store.updateMemberLevel(memberLevel)

      // Free用户访客≥3时显示升级提示
      const showUpgradeHint = memberLevel === 'free' && (stats.visitors >= 3 || recommendData.length >= 3)

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
        showEmpty: !brochure && (!Array.isArray(recommendData) || recommendData.length === 0),
        showUpgradeHint,
        visitorList: [],
        loading: false,
      })

      Logger.info('首页', '数据加载完成')
    } catch (err) {
      Logger.error('首页', '加载失败', err)
      this.setData({ loading: false })
    }
  },

  toggleSceneMode() {
    this.setData({
      sceneModeExpanded: !this.data.sceneModeExpanded,
    })
  },

  selectSceneMode(e) {
    const mode = e.currentTarget.dataset.mode
    this.setData({
      sceneMode: mode,
    })
    wx.showToast({ title: '已切换至' + (mode === 'personal' ? '个人展示' : mode === 'business' ? '商务对接' : '社交拓展') + '模式', icon: 'none' })
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

  // 跳转升级会员
  goMembership() {
    wx.navigateTo({ url: '/pages/membership/index' })
  },

  shareCard() {
    wx.shareAppMessage({
      title: this.data.userInfo.name + '的AI数智名片',
      path: this.data.brochure ? `/pages/brochure/preview/index?id=${this.data.brochure.id}` : '/pages/index/index',
    })
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

  goAICenter() {
    wx.navigateTo({ url: '/pages/ai/index/index' })
  },

  onShareAppMessage() {
    const brochure = this.data.brochure
    return {
      title: this.data.userInfo.name + '的AI数智名片',
      path: brochure ? `/pages/brochure/preview/index?id=${brochure.id}` : '/pages/index/index',
    }
  },
})