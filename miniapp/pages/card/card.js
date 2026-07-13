/**
 * 名片页
 * 支持两种模式：
 *  - 'list': tabBar 进入时展示当前用户的名片列表
 *  - 'detail': 从其他页面传入 id 时展示具体名片详情 (i18n enabled)
 */
const { MockService } = require('../../utils/mockService')
const { miniappApi } = require('../../utils/api')
const store = require('../../utils/store')
const i18n = require('../../utils/i18n')

Page({
  data: {
    // 通用
    loading: true,
    mode: 'list',       // 'list' | 'detail'
    _t: {},

    // 列表模式
    myCards: [],
    listError: false,

    // 详情模式
    card: null,
    stats: { views: 0, visitors: 0, matches: 0, trust: 0 },
    purposeText: '',
  },

  onLoad(options) {
    this._loadI18n()
    const cardId = options && options.id
    if (cardId) {
      this.setData({ mode: 'detail' })
      this.loadCardDetail(cardId)
    } else {
      // tab 进入，展示用户自己的名片列表
      this.setData({ mode: 'list' })
      this.loadMyCards()
    }
  },

  onShow() {
    this._loadI18n()
    // 每次显示时刷新列表（如果处于列表模式且有变化可能）
    if (this.data.mode === 'list' && !this.data.loading) {
      this.loadMyCards(true) // silent refresh
    }
  },

  /** 加载国际化翻译 */
  _loadI18n() {
    this.setData({ _t: i18n.getTranslations() })
  },

  // ======================== 列表模式 ========================

  /** 获取当前用户的名片列表 */
  async loadMyCards(silent = false) {
    if (!silent) this.setData({ loading: true, listError: false })
    try {
      const state = store.getState()
      const userInfo = state.userInfo
      if (!userInfo || !userInfo.id) {
        console.warn('[card] 无用户信息，跳转登录页')
        this.setData({ myCards: [], loading: false, listError: true })
        wx.switchTab({ url: '/pages/profile/profile' })
        return
      }
      const { brochureApi } = require('../../utils/api')
      const res = await brochureApi.list()
      // MockService 返回 { data: [...] }，真实API也同理
      const allBrochures = Array.isArray(res) ? res : (res?.data || [])
      // 按当前用户过滤
      const myCards = allBrochures.filter(b => String(b.user_id) === String(userInfo.id))
      // 按浏览数降序排列
      myCards.sort((a, b) => (b.view_count || 0) - (a.view_count || 0))
      this.setData({ myCards, loading: false })
    } catch (err) {
      console.error('[card] 加载名片列表失败:', err)
      this.setData({ myCards: [], loading: false, listError: true })
    }
  },

  /** 选中一张名片 → 切到详情模式 */
  selectCard(e) {
    const id = e?.currentTarget?.dataset?.id
    if (!id) return
    this.setData({ mode: 'detail' })
    this.loadCardDetail(id)
  },

  /** 从详情切回列表 */
  backToList() {
    this.setData({ mode: 'list', card: null })
    this.loadMyCards()
  },

  /** 创建新名片 */
  handleEmptyAction() {
    if (this.data.listError) {
      this.loadMyCards()
    } else {
      this.createCard()
    }
  },

  createCard() {
    wx.navigateTo({ url: '/pages/brochure/create/index' })
  },

  // ======================== 详情模式 ========================

  async loadCardDetail(cardId) {
    this.setData({ loading: true })
    try {
      const [brochure, recommendData, trustNet] = await Promise.all([
        MockService.getBrochureById(cardId),
        MockService.getRecommendList().catch(() => []),
        MockService.getTrustNetwork().catch(() => ({ trusting: [], trusted_by: [] })),
      ])
      
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
          user_name: brochure.user_name || brochure.name || '',
          user_company: brochure.user_company || brochure.company || '',
          user_title: brochure.user_title || brochure.title || '',
          user_avatar: brochure.user_avatar || brochure.avatar || '',
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
        const vStats = await MockService.getVisitorStats(cardId)
        stats.views = vStats.view_count || 0
        stats.visitors = vStats.total_visits || 0
        const recommendList = Array.isArray(recommendData) ? recommendData : (recommendData?.data || [])
        stats.matches = recommendList.length || 0
        const trustData = trustNet.data || trustNet
        stats.trust = (trustData.trusting?.length || 0) + (trustData.trusted_by?.length || 0)
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
    if (card) {
      wx.navigateTo({ url: `/pages/brochure/preview/index?id=${card.id}` })
    }
  },

  shareCard() {
    const card = this.data.card
    if (typeof wx.shareAppMessage === 'function') {
      wx.shareAppMessage({
        title: (card?.user_name || '') + '的AI数智名片',
        path: card ? `/pages/brochure/preview/index?id=${card.id}` : '/pages/index/index',
      })
    } else {
      wx.showToast({ title: '当前版本不支持主动分享', icon: 'none' })
    }
  },

  async generateQRCode() {
    const card = this.data.card
    if (!card) return
    try {
      const { miniappApi } = require('../../utils/api')
      const res = await miniappApi.getQRCode(card.share_token)
      if (res?.qrcode_url) {
        wx.previewImage({ urls: [res.qrcode_url] })
      } else {
        wx.showToast({ title: '生成失败', icon: 'none' })
      }
    } catch (err) {
      console.error('生成二维码失败:', err)
    }
  },

  onShareAppMessage() {
    const card = this.data.card
    if (this.data.mode === 'list' || !card) {
      return {
        title: 'AI数智名片 - 智能商务连接',
        path: '/pages/index/index',
      }
    }
    return {
      title: (card?.user_name || '') + '的AI数智名片',
      path: card ? `/pages/brochure/preview/index?id=${card.id}` : '/pages/index/index',
    }
  },
})
