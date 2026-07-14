/**
 * 首页 - 名片列表 + 推荐
 * 使用MockService获取数据
 */
const { MockService } = require('../../utils/mockService')
const { brochureApi, platformApi } = require('../../utils/api')
const store = require('../../utils/store')
const i18n = require('../../utils/i18n')
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
    showBusinessCards: true,
    showPlatform: false,
    showTrustNetwork: false,
    platformRecommend: [],
    platformLoading: false,

    // 新手引导
    showOnboarding: false,
    onboardingStep: 1,
    onboardingSteps: [],

    // i18n
    _t: {},
  },

  onLoad(options) {
    Logger.info('首页', '页面加载')
    this._loadI18n()
    
    const state = store.getState()
    Logger.info('首页', '当前状态', { 
      isLoggedIn: state.isLoggedIn, 
      hasUserInfo: !!state.userInfo,
      userName: state.userInfo?.name || state.userInfo?.nickName || '无'
    })
    
    // 登录守卫：未登录时跳转登录页
    if (!state.isLoggedIn) {
      wx.redirectTo({ url: '/pages/login/index' })
      return
    }
    
    this.loadPageData()
    this.loadPlatformRecommend()
  },

  async loadPlatformRecommend() {
    this.setData({ platformLoading: true })
    try {
      const res = await platformApi.list()
      const data = Array.isArray(res) ? res : (res.data || [])
      const platforms = data.slice(0, 4).map((p, index) => ({
        id: p.id,
        name: p.name,
        desc: p.description || '',
        logoLetter: p.name ? p.name[0] : 'P',
        resourceCount: p.resource_count || 0,
        annualFee: p.annual_fee,
        rank: index + 1,
      }))
      this.setData({ platformRecommend: platforms, platformLoading: false })
    } catch (err) {
      console.error('[首页] 加载平台推荐失败:', err)
      this.setData({ platformLoading: false })
    }
  },

  onShow() {
    const state = store.getState()
    const { isLoggedIn } = state
    // 全局登录守卫（第二层）：页面级 — 未登录时跳回登录页
    if (!isLoggedIn) {
      wx.redirectTo({ url: '/pages/login/index' })
      return
    }
    if (state.dataDirty || !this.data.loading) {
      store.clearDataDirty()
      this.loadPageData()
    }
    this._loadI18n()
  },

  /** 加载国际化翻译 */
  _loadI18n() {
    this.setData({
      _t: i18n.getTranslations(),
      onboardingSteps: [
        { icon: '✎', title: i18n.t('guideStep1Title'), desc: i18n.t('guideStep1Desc') },
        { icon: '◇', title: i18n.t('guideStep2Title'), desc: i18n.t('guideStep2Desc') },
        { icon: '↗', title: i18n.t('guideStep3Title'), desc: i18n.t('guideStep3Desc') },
      ],
    })
  },

  /** 检查是否需要展示新手引导 */
  _checkOnboarding() {
    if (store.isOnboardingNeeded() && !this.data.showOnboarding) {
      this.setData({ showOnboarding: true, onboardingStep: 1 })
    }
  },

  /** 带超时和重试的数据获取包装 */
  async _fetchWithRetry(fn, fallback, maxRetries = 2, timeoutMs = 8000) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const result = await Promise.race([
          fn(),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error(`timeout after ${timeoutMs}ms`)), timeoutMs)
          ),
        ])
        if (attempt > 1) Logger.info('首页', `第${attempt}次重试成功`)
        return result
      } catch (err) {
        Logger.warn('首页', `第${attempt}/${maxRetries}次失败`, err.message || err)
        if (attempt < maxRetries) {
          const delay = Math.min(500 * Math.pow(2, attempt - 1), 3000)
          await new Promise(r => setTimeout(r, delay))
        }
      }
    }
    Logger.warn('首页', '已耗尽重试次数，使用降级数据')
    return fallback
  },

  async loadPageData() {
    this.setData({ loading: true })
    
    const storedState = store.getState()
    const storedUserInfo = storedState.userInfo || {}
    
    try {
      Logger.info('首页', '开始加载数据')
      
      let profileRes, brochuresRes, trustNetRes, recommendRes
      try {
        [profileRes, brochuresRes, trustNetRes, recommendRes] = await Promise.all([
          this._fetchWithRetry(
            () => MockService.getUserProfile(),
            { data: { userInfo: {}, memberLevel: 'free' } },
          ),
          this._fetchWithRetry(
            () => MockService.getBrochures(),
            { data: [] },
          ),
          this._fetchWithRetry(
            () => MockService.getTrustNetwork(),
            { data: { trusting: [], trusted_by: [] } },
          ),
          this._fetchWithRetry(
            () => MockService.getRecommendList(),
            { data: [] },
          ),
        ])
        Logger.info('首页', 'API数据加载完成')
      } catch (apiErr) {
        Logger.warn('首页', 'API加载失败，使用本地数据', apiErr)
        profileRes = { data: { userInfo: {}, memberLevel: 'free' } }
        brochuresRes = { data: [] }
        trustNetRes = { data: { trusting: [], trusted_by: [] } }
        recommendRes = { data: [] }
      }

      const profile = profileRes && profileRes.data ? profileRes.data : profileRes
      const brochuresList = brochuresRes && brochuresRes.data ? brochuresRes.data : brochuresRes
      const trustData = trustNetRes && trustNetRes.data ? trustNetRes.data : trustNetRes
      const recommendData = recommendRes && recommendRes.data ? recommendRes.data : recommendRes

      const userInfoData = profile.userInfo || profile
      const brochure = Array.isArray(brochuresList) ? brochuresList[0] : null

      const trustList = trustData.trusting || []
      const trustCount = trustList.length

      let stats = { visitors: 0, matches: recommendData.length, trust: trustCount }

      if (brochure) {
        this._fetchWithRetry(
          () => MockService.getVisitorStats(),
          { data: { total_visits: 0, total: 0 } },
        ).then(vStatsRes => {
          const vStats = vStatsRes && vStatsRes.data ? vStatsRes.data : vStatsRes
          if (vStats) {
            this.setData({
              stats: { ...this.data.stats, visitors: vStats.total_visits || vStats.total || 0 },
            })
          }
        }).catch(() => {})
      }

      const userInfo = {
        name: storedUserInfo.name || storedUserInfo.nickName || userInfoData.name || '微信用户',
        avatar: storedUserInfo.avatar || storedUserInfo.avatarUrl || userInfoData.avatar || '',
        company: storedUserInfo.company || userInfoData.company || '',
        title: storedUserInfo.title || userInfoData.title || '',
      }

      const { getLevelText } = require('../../utils/levels')
      const memberLevel = profile.memberLevel || storedState.memberLevel || 'free'
      const memberLevelText = getLevelText(memberLevel)

      store.updateUserInfo(userInfo)
      store.updateMemberLevel(memberLevel)

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
          upgradeHintText: i18n.t('upgradeHint', { count: stats.visitors }),
          visitorList: [],
          loading: false,
        })

      Logger.info('首页', '数据加载完成', { userName: userInfo.name, hasAvatar: !!userInfo.avatar })

      this._checkOnboarding()
    } catch (err) {
      Logger.error('首页', '加载失败', err)
      console.error('[首页] loadPageData 错误:', err)
      
      const userInfo = {
        name: storedUserInfo.name || storedUserInfo.nickName || '微信用户',
        avatar: storedUserInfo.avatar || storedUserInfo.avatarUrl || '',
        company: storedUserInfo.company || '',
        title: storedUserInfo.title || '',
      }
      
      const { getLevelText } = require('../../utils/levels')
      const memberLevel = storedState.memberLevel || 'free'
      const memberLevelText = getLevelText(memberLevel)
      
      this.setData({
        userInfo,
        memberLevel,
        memberLevelText,
        stats: { visitors: 0, matches: 0, trust: 0 },
        brochure: null,
        trustCount: 0,
        trustList: [],
        recommendList: [],
        showEmpty: true,
        showUpgradeHint: false,
        visitorList: [],
        loading: false,
      })
    }
  },

  toggleSceneMode() {
    this.setData({
      sceneModeExpanded: !this.data.sceneModeExpanded,
    })
  },

  selectSceneMode(e) {
    const mode = e.currentTarget.dataset.mode
    const sceneConfig = {
      personal: { showBusinessCards: true, showPlatform: false, showTrustNetwork: false, showRecommend: true },
      business: { showBusinessCards: true, showPlatform: true, showTrustNetwork: false, showRecommend: true },
      social: { showBusinessCards: false, showPlatform: false, showTrustNetwork: true, showRecommend: true },
    }
    this.setData({
      sceneMode: mode,
      ...sceneConfig[mode],
    })
    const modeNames = { personal: i18n.t('modePersonal'), business: i18n.t('modeBusiness'), social: i18n.t('modeSocial') }
    wx.showToast({ title: i18n.t('switchedTo') + modeNames[mode] + i18n.t('modeSuffix'), icon: 'none' })
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
    if (typeof wx.shareAppMessage === 'function') {
      wx.shareAppMessage({
        title: this.data.userInfo.name + '的AI数智名片',
        path: this.data.brochure ? `/pages/brochure/preview/index?id=${this.data.brochure.id}` : '/pages/index/index',
      })
    } else {
      wx.showToast({ title: '当前版本不支持主动分享', icon: 'none' })
    }
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
    const id = e.currentTarget.dataset.id
    if (id) {
      wx.navigateTo({ url: `/pages/platform/detail/index?id=${id}` })
    }
  },

  // 查看更多平台
  goPlatformList() {
    wx.navigateTo({ url: '/pages/platform/list/index' })
  },

  goAICenter() {
    wx.navigateTo({ url: '/pages/ai/index/index' })
  },

  /** 新手引导 - 下一步 */
  nextStep() {
    const next = this.data.onboardingStep + 1
    if (next > 3) {
      this.closeOnboarding()
    } else {
      this.setData({ onboardingStep: next })
    }
  },

  /** 新手引导 - 上一步 */
  prevStep() {
    if (this.data.onboardingStep > 1) {
      this.setData({ onboardingStep: this.data.onboardingStep - 1 })
    }
  },

  /** 新手引导 - 关闭并标记完成 */
  closeOnboarding() {
    this.setData({ showOnboarding: false, onboardingStep: 1 })
    store.setOnboardingDone()
  },

  /** 新手引导 - 跳过 */
  skipOnboarding() {
    this.setData({ showOnboarding: false, onboardingStep: 1 })
    store.setOnboardingDone()
    wx.showToast({ title: i18n.t('guideSkipped'), icon: 'none' })
  },

  onShareAppMessage() {
    const brochure = this.data.brochure
    return {
      title: this.data.userInfo.name + '的AI数智名片',
      path: brochure ? `/pages/brochure/preview/index?id=${brochure.id}` : '/pages/index/index',
    }
  },
})