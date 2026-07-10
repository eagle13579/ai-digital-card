/**
 * 首页 - 名片列表 + 推荐
 * 增加：Free用户使用接近上限时显示智能升级提示条
 */
const { MockService } = require('../../utils/mockService')
const { Logger } = require('../../utils/util')

Page({
  data: {
    loading: true,
    _dataLoaded: false,
    userInfo: {},
    memberLevel: 'free',
    memberLevelText: 'Free',
    stats: { visitors: 0, matches: 0, trust: 0 },
    brochure: null,
    trustCount: 0,
    trustList: [],
    recommendList: [],
    visitorList: [],

    // 升级提示
    showUpgradeHint: false,
    upgradeHintText: '',

    // 场景模式
    showSceneSelector: true,
    currentScene: 'online',

    // 平台推荐（静态UI数据，非后端数据）
    platformRecommend: [
      { id: 1, name: 'AI技术合作平台', desc: 'AI技术开发·模型训练·数据标注', icon: '🤖', bg: 'linear-gradient(135deg, #667eea, #764ba2)' },
      { id: 2, name: '供应链资源平台', desc: '供应商对接·物流配送·仓储服务', icon: '🚚', bg: 'linear-gradient(135deg, #f093fb, #f5576c)' },
      { id: 3, name: '投融资对接平台', desc: '天使投资·VC融资·并购重组', icon: '💰', bg: 'linear-gradient(135deg, #4facfe, #00f2fe)' },
      { id: 4, name: '市场营销平台', desc: '品牌推广·渠道拓展·流量获客', icon: '📢', bg: 'linear-gradient(135deg, #43e97b, #38f9d7)' },
    ],
  },

  onLoad(options) {
    const app = getApp()
    // 未登录时跳转登录页
    if (!app.globalData.token) {
      Logger.info('首页', '未登录, 跳转登录页')
      wx.reLaunch({ url: '/pages/login/index' })
      return
    } else {
      Logger.info('首页', '页面加载')
      // 恢复场景偏好
      const scenePrefs = wx.getStorageSync('scene_prefs')
      if (scenePrefs && scenePrefs.scene) {
        this.setData({ currentScene: scenePrefs.scene })
      }
      // 首次使用弹出场景建议
      const firstTime = wx.getStorageSync('scene_first_time')
      if (firstTime === '' || firstTime === undefined || firstTime === null) {
        wx.showModal({
          title: '场景模式',
          content: '欢迎使用！您可以选择适合您的场景模式，我们将为您提供更贴心的服务。',
          confirmText: '去选择',
          success: (res) => {
            if (res.confirm) {
              wx.setStorageSync('scene_first_time', false)
            }
          }
        })
      }
      this.loadPageData()
    }
  },

  onShow() {
    const app = getApp()
    if (app.globalData.token) {
      // 检查是否有数据更新标记（如从创建页返回）
      if (app.globalData._dataDirty) {
        app.globalData._dataDirty = false
        this.loadPageData()
      } else if (!this.data._dataLoaded) {
        this.loadPageData()
      }
    }
  },

  /**
   * 加载首页全部数据
   * 并行请求：用户信息、名片、信任网络、推荐列表
   */
  async loadPageData() {
    this.setData({ loading: true })
    try {
      const [profile, brochures, trustNet, recommend] = await Promise.all([
        MockService.getUserProfile(),
        MockService.getBrochures(),
        MockService.getTrustNetwork(),
        MockService.getRecommendList(),
      ])

      const profileData = profile.data !== undefined ? profile.data : profile
      const userInfoData = profileData.userInfo || profileData || {}

      const userInfo = {
        name: userInfoData.name || '',
        avatar: userInfoData.avatar || '',
        company: userInfoData.company || '',
        title: userInfoData.title || '',
      }

      const memberLevel = profileData.memberLevel || userInfoData.memberLevel || 'free'
      const memberLevelText = { free: 'Free', gold: 'Gold', diamond: 'Diamond', board: 'Board' }[memberLevel] || 'Free'

      const app = getApp()
      app.updateUserInfo(userInfo)
      app.updateMemberLevel(memberLevel)

      let brochuresList = []
      if (Array.isArray(brochures)) {
        brochuresList = brochures
      } else if (brochures.data && Array.isArray(brochures.data)) {
        brochuresList = brochures.data
      }
      const brochure = brochuresList.length > 0 ? brochuresList[0] : null

      const trustData = trustNet.data !== undefined ? trustNet.data : (trustNet || {})
      const trustList = trustData.trusting || []
      const trustCount = trustList.length

      let recommendData = []
      if (Array.isArray(recommend)) {
        recommendData = recommend
      } else if (recommend.data && Array.isArray(recommend.data)) {
        recommendData = recommend.data
      }

      let visitors = 0
      if (brochure) {
        try {
          const vStatsRes = await MockService.getVisitorStats()
          const vStats = vStatsRes.data !== undefined ? vStatsRes.data : vStatsRes
          visitors = vStats.total_visits || vStats.total || vStats.visitors || 0
        } catch (e) {
          Logger.warn('首页', '获取访客统计失败', e)
        }
      }

      let showUpgradeHint = false
      let upgradeHintText = ''

      // ===== 7. 组装统计数据 =====
      const stats = {
        visitors: visitors,
        matches: recommendData.length,
        trust: trustCount,
      }

      // ===== 8. 更新页面数据 =====
      this.setData({
        userInfo,
        memberLevel: memberLevel,
        memberLevelText: { free: 'Free', pro: 'Pro', enterprise: 'Enterprise' }[memberLevel] || 'Free',
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
        recommendList: recommendData.slice(0, 3),
        visitorList: [],
        showUpgradeHint,
        upgradeHintText,
        loading: false,
        _dataLoaded: true,
      })

      Logger.info('首页', '数据加载完成', { stats, recommendCount: recommendData.length })
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
    wx.showModal({
      title: '提示',
      content: '平台详情功能即将开放，敬请期待',
      showCancel: false
    })
  },

  // 跳转会员中心
  goUpgrade() {
    wx.navigateTo({ url: '/pages/membership/membership' })
  },

  /** 跳转AI能力中心 */
  goAiCenter() {
    wx.navigateTo({ url: '/pages/ai/index' })
  },

  // 关闭升级提示
  closeUpgradeHint() {
    this.setData({ showUpgradeHint: false })
  },

  // 场景模式切换
  onSceneChange(e) {
    const sceneType = e.detail.scene_type
    this.setData({ currentScene: sceneType })
    wx.setStorageSync('scene_prefs', { scene: sceneType })
  },

  onShareAppMessage() {
    const brochure = this.data.brochure
    return {
      title: this.data.userInfo.name + '的AI数智名片',
      path: brochure ? `/pages/brochure/preview/index?id=${brochure.id}` : '/pages/index/index',
    }
  },
})
