/**
 * 首页 - 名片列表 + 推荐
 * 使用真实API获取数据
 */
const { userApi, brochureApi, matchApi, trustApi, visitorApi, platformApi } = require('../../utils/api')
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
    this.loadPageData()
    this.loadPlatformRecommend()
  },

  async loadPlatformRecommend() {
    this.setData({ platformLoading: true })
    try {
      const res = await platformApi.list().catch(() => null)
      const platforms = (res || []).slice(0, 4).map((p, index) => ({
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
    const { isLoggedIn, dataDirty } = store.getState()
    if (isLoggedIn) {
      if (dataDirty || !this.data.loading) {
        store.clearDataDirty()
        this.loadPageData()
      }
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

  async loadPageData() {
    this.setData({ loading: true })
    try {
      const [profile, brochures, trustNet, recommend] = await Promise.all([
        userApi.getProfile({ noToast: true }).catch(() => ({ userInfo: {}, memberLevel: 'free' })),
        brochureApi.list({}, { noToast: true }).catch(() => []),
        trustApi.getNetwork({ noToast: true }).catch(() => ({ trusting: [], trusted_by: [] })),
        matchApi.getRecommendList(1, 10, { noToast: true }).catch(() => []),
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
        visitorApi.getStats(brochure.id).then(vStats => {
          if (vStats) {
            this.setData({
              stats: { ...this.data.stats, visitors: vStats.total_visits || vStats.total || 0 },
            })
          }
        }).catch(() => {})
      }

      const store = require('../../utils/store')
      const storedUserInfo = store.getState().userInfo || {}
      const userInfo = {
        name: storedUserInfo.name || storedUserInfo.nickName || userInfoData.name || '',
        avatar: storedUserInfo.avatar || storedUserInfo.avatarUrl || userInfoData.avatar || '',
        company: storedUserInfo.company || userInfoData.company || '',
        title: storedUserInfo.title || userInfoData.title || '',
      }

      const { getLevelText } = require('../../utils/levels')
      const memberLevel = profile.memberLevel || 'free'
      const memberLevelText = getLevelText(memberLevel)

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
          upgradeHintText: i18n.t('upgradeHint', { count: stats.visitors }),
          visitorList: [],
          loading: false,
        })

      Logger.info('首页', '数据加载完成')

      // 加载完成后检查新手引导
      this._checkOnboarding()
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