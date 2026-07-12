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
    const cardId = options.id
    if (cardId) {
      this.loadCardDetail(cardId)
    } else {
      wx.showToast({ title: i18n.t('paramError'), icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
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
    return {
      title: (card?.user_name || '') + '的AI数智名片',
      path: card ? `/pages/brochure/preview/index?id=${card.id}` : '/pages/index/index',
    }
  },
})
