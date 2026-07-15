/**
 * 名片详情页
 * 展示单张名片的详细信息与统计数据 (i18n enabled)
 */
const { MockService } = require('../../utils/mockService')
const { miniappApi } = require('../../utils/api')
const i18n = require('../../utils/i18n')

Page({
  data: {
    loading: true,
    card: null,
    stats: { views: 0, visitors: 0, matches: 0, trust: 0 },
    purposeText: '',
    // i18n
    _t: {},
  },

  onLoad(options) {
    this._loadI18n()
    // 登录守卫
    const store = require('../../utils/store')
    if (!store.getState().isLoggedIn) {
      wx.redirectTo({ url: '/pages/login/index' })
      return
    }
    const cardId = options.id
    if (cardId) {
      this.loadCardDetail(cardId)
    } else {
      // 从tab进入时没有传id，加载用户自己的名片
      this.loadMyCard()
    }
  },

  async loadMyCard() {
    this.setData({ loading: true })
    try {
      const brochures = await MockService.getMyBrochures()
      const list = Array.isArray(brochures) ? brochures : (brochures?.data?.items || [])
      if (list.length > 0) {
        // 已有画册，直接跳转到预览页（同首页名片预览的指向）
        const first = list[0]
        wx.redirectTo({ url: `/pages/brochure/preview/index?id=${first.id}` })
      } else {
        // 无名片，跳转创建页
        wx.redirectTo({ url: '/pages/brochure/create/index' })
      }
    } catch (err) {
      console.error('加载我的名片失败:', err)
      this.setData({ loading: false })
    }
  },

  onShow() {
    this._loadI18n()
  },

  /** 加载国际化翻译 */
  _loadI18n() {
    this.setData({ _t: i18n.getTranslations() })
  },

  async loadCardDetail(cardId) {
    this.setData({ loading: true })
    const store = require('../../utils/store')
    const { userInfo: storeUserInfo } = store.getState()
    try {
      const [brochure, recommendRes, trustNetRes] = await Promise.all([
        MockService.getBrochureById(cardId),
        MockService.getRecommendList().catch(() => ({ data: [] })),
        MockService.getTrustNetwork().catch(() => ({ data: { trusting: [], trusted_by: [] } })),
      ])
      
      const recommendData = recommendRes && recommendRes.data ? recommendRes.data : recommendRes
      const trustNet = trustNetRes && trustNetRes.data ? trustNetRes.data : trustNetRes
      
      // 从画册的 profile 页面 content 中提取用户信息
      let profileName = '', profileAvatar = '', profileCompany = '', profileTitle = ''
      if (brochure && brochure.pages && Array.isArray(brochure.pages)) {
        const profilePage = brochure.pages.find(p => p.content_type === 'profile')
        if (profilePage && profilePage.content) {
          try {
            const parsed = JSON.parse(profilePage.content)
            profileName = parsed.name || ''
            profileAvatar = ''  // avatar 存在 brochure.cover 中，不在 content 里
            profileCompany = parsed.company || ''
            profileTitle = parsed.title || ''
          } catch (e) {}
        }
      }
      // avatar 优先用 brochure.cover，其次 store
      const avatar = brochure?.cover || storeUserInfo?.avatar || storeUserInfo?.avatarUrl || ''
      
      let card = null
      if (brochure) {
        card = {
          id: brochure.id,
          user_id: brochure.user_id,
          title: brochure.title,
          cover: brochure.cover,
          purpose: brochure.purpose,
          status: brochure.status,
          share_token: brochure.share_token,
          view_count: brochure.view_count || 0,
          user_name: profileName || storeUserInfo?.name || storeUserInfo?.nickName || '',
          user_company: profileCompany || storeUserInfo?.company || '',
          user_title: profileTitle || storeUserInfo?.title || '',
          user_avatar: avatar,
        }
      }

      const purposeMap = {
        partner: i18n.t('choosePartner'),
        investor: i18n.t('chooseInvest'),
        employee: i18n.t('chooseTalent'),
        client: i18n.t('chooseClient'),
        friend: i18n.t('chooseFriend'),
      }
      const purposeText = purposeMap[card && card.purpose] || (card && card.purpose) || ''

      let stats = { views: 0, visitors: 0, matches: 0, trust: 0 }
      if (card) {
        const vStatsRes = await MockService.getVisitorStats(cardId)
        const vStats = vStatsRes && vStatsRes.data ? vStatsRes.data : vStatsRes
        stats.views = vStats.view_count || 0
        stats.visitors = vStats.total_visits || 0
        const recommendList = Array.isArray(recommendData) ? recommendData : []
        stats.matches = recommendList.length || 0
        stats.trust = (trustNet.trusting?.length || 0) + (trustNet.trusted_by?.length || 0)
      }

      this.setData({
        card,
        stats,
        purposeText,
        loading: false,
      })
    } catch (err) {
      console.error('加载名片详情失败:', err)
      this.setData({ loading: false })
    }
  },

  goPreview() {
    const card = this.data.card
    if (card && card.id) {
      wx.navigateTo({ url: `/pages/brochure/preview/index?id=${card.id}` })
    } else {
      wx.navigateTo({ url: '/pages/brochure/create/index' })
    }
  },

  shareCard() {
    const card = this.data.card
    wx.showToast({ title: '请点击右上角"..."分享', icon: 'none' })
  },

  onShareAppMessage() {
    const card = this.data.card
    return {
      title: (card?.user_name || '') + '的AI数智名片',
      path: card ? `/pages/brochure/preview/index?id=${card.id}` : '/pages/index/index',
    }
  },
})
