/**
 * 首页 - 名片列表 + 推荐
 * 连接后端真实API（/api/v1/ 前缀）
 * 增加：Free用户使用接近上限时显示智能升级提示条
 */
const { userApi, brochureApi, trustApi, matchApi, visitorApi, membershipApi } = require('../../utils/api')
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

    // 升级提示
    showUpgradeHint: false,
    upgradeHintText: '',

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
      if (app.globalData.__DEV_MODE__) {
        Logger.info('首页', '开发模式: 未登录, 显示空白状态')
        this.setData({ loading: false })
      } else {
        wx.navigateTo({ url: '/pages/login/index' })
        return
      }
    } else {
      Logger.info('首页', '页面加载')
      this.loadPageData()
    }
  },

  onShow() {
    const app = getApp()
    if (app.globalData.token && !this.data.loading) {
      this.loadPageData()
    }
  },

  /**
   * 加载首页全部数据
   * 并行请求：用户信息、名片、信任网络、推荐列表、会员状态
   */
  async loadPageData() {
    this.setData({ loading: true })
    try {
      // ===== 并行请求全部数据 =====
      const [
        profileRes,
        brochuresRes,
        trustNetRes,
        recommendRes,
        membershipRes,
      ] = await Promise.all([
        // 1. 用户信息
        userApi.getProfile().catch(err => {
          Logger.warn('首页', '获取用户信息失败，使用默认值', err)
          return null
        }),
        // 2. 名片/画册列表
        brochureApi.list({ page: 1, size: 10 }).catch(err => {
          Logger.warn('首页', '获取画册列表失败', err)
          return null
        }),
        // 3. 信任网络
        trustApi.getNetwork().catch(err => {
          Logger.warn('首页', '获取信任网络失败', err)
          return null
        }),
        // 4. 推荐匹配列表
        matchApi.getRecommend({ page: 1, size: 10 }).catch(err => {
          Logger.warn('首页', '获取推荐列表失败', err)
          return null
        }),
        // 5. 会员状态（用于升级提示）
        membershipApi.getStatus().catch(err => {
          Logger.warn('首页', '获取会员状态失败', err)
          return null
        }),
      ])

      // ===== 1. 解析用户信息 =====
      const profileData = profileRes?.data !== undefined ? profileRes.data : profileRes
      const userInfoData = profileData?.userInfo || profileData || {}

      const userInfo = {
        name: userInfoData.name || '',
        avatar: userInfoData.avatar || '',
        company: userInfoData.company || '',
        title: userInfoData.title || '',
      }

      const memberLevel = profileData?.memberLevel || userInfoData.memberLevel || 'free'
      const memberLevelText = { free: 'Free', pro: 'Pro', enterprise: 'Enterprise' }[memberLevel] || 'Free'

      const app = getApp()
      app.updateUserInfo(userInfo)
      app.updateMemberLevel(memberLevel)

      // ===== 2. 解析名片/画册 =====
      let brochuresList = []
      if (Array.isArray(brochuresRes)) {
        brochuresList = brochuresRes
      } else if (brochuresRes?.data && Array.isArray(brochuresRes.data)) {
        brochuresList = brochuresRes.data
      } else if (brochuresRes?.items && Array.isArray(brochuresRes.items)) {
        brochuresList = brochuresRes.items
      } else if (brochuresRes?.list && Array.isArray(brochuresRes.list)) {
        brochuresList = brochuresRes.list
      }
      const brochure = brochuresList.length > 0 ? brochuresList[0] : null

      // ===== 3. 解析信任网络 =====
      const trustData = trustNetRes?.data !== undefined ? trustNetRes.data : (trustNetRes || {})
      const trustList = trustData.trusting || []
      const trustCount = trustList.length

      // ===== 4. 解析推荐列表 =====
      let recommendData = []
      if (Array.isArray(recommendRes)) {
        recommendData = recommendRes
      } else if (recommendRes?.data && Array.isArray(recommendRes.data)) {
        recommendData = recommendRes.data
      } else if (recommendRes?.items && Array.isArray(recommendRes.items)) {
        recommendData = recommendRes.items
      } else if (recommendRes?.list && Array.isArray(recommendRes.list)) {
        recommendData = recommendRes.list
      }

      // ===== 5. 获取访客统计（需要 brochureId） =====
      let visitors = 0
      if (brochure) {
        try {
          const vStatsRes = await visitorApi.getStats(brochure.id)
          const vStats = vStatsRes?.data !== undefined ? vStatsRes.data : vStatsRes
          visitors = vStats?.total_visits || vStats?.total || vStats?.visitors || 0
        } catch (e) {
          Logger.warn('首页', '获取访客统计失败', e)
        }
      }

      // ===== 6. 解析会员状态 → 升级提示 =====
      const membership = membershipRes?.data ?? membershipRes ?? {}
      const memLevel = membership.tier || membership.level || memberLevel
      const ocrCount = membership.ocr_count ?? membership.ocrCount ?? 0
      const ocrLimit = membership.ocr_limit ?? membership.ocrLimit ?? (memLevel === 'free' ? 3 : 100)
      const cardCount = membership.card_count ?? membership.cardCount ?? (brochuresList.length || 0)
      const cardLimit = membership.card_limit ?? membership.cardLimit ?? (memLevel === 'free' ? 1 : 10)

      let showUpgradeHint = false
      let upgradeHintText = ''

      if (memLevel === 'free') {
        // Free用户：检查使用是否接近上限
        const ocrRatio = ocrLimit > 0 ? ocrCount / ocrLimit : 0
        const cardRatio = cardLimit > 0 ? cardCount / cardLimit : 0
        const maxRatio = Math.max(ocrRatio, cardRatio)

        if (maxRatio >= 0.8) {
          showUpgradeHint = true
          if (ocrRatio >= 0.8) {
            const remaining = ocrLimit - ocrCount
            upgradeHintText = `您本月OCR还剩${remaining}次，升级Pro享100次/月`
          } else if (cardRatio >= 0.8) {
            upgradeHintText = `名片已达${cardCount}/${cardLimit}张，升级Pro可创建更多`
          } else {
            upgradeHintText = '使用接近上限，升级Pro解锁更多权益'
          }
        }
      }

      // ===== 7. 组装统计数据 =====
      const stats = {
        visitors: visitors,
        matches: recommendData.length,
        trust: trustCount,
      }

      // ===== 8. 更新页面数据 =====
      this.setData({
        userInfo,
        memberLevel: memLevel,
        memberLevelText: { free: 'Free', pro: 'Pro', enterprise: 'Enterprise' }[memLevel] || 'Free',
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
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  shareCard() {
    wx.showShareMenu({ withShareTicket: true })
  },

  goTrust() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  goMatch() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  goMatchDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.showToast({ title: '功能开发中', icon: 'none' })
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

  // 跳转会员中心
  goUpgrade() {
    wx.navigateTo({ url: '/pages/membership/membership' })
  },

  // 关闭升级提示
  closeUpgradeHint() {
    this.setData({ showUpgradeHint: false })
  },

  onShareAppMessage() {
    const brochure = this.data.brochure
    return {
      title: this.data.userInfo.name + '的AI数智名片',
      path: brochure ? `/pages/brochure/preview/index?id=${brochure.id}` : '/pages/index/index',
    }
  },
})
