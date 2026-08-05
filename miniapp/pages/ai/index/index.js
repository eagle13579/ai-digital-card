const store = require('../../../utils/store')
const i18n = require('../../../utils/i18n')

Page({
  data: {
    features: [],
    isLoggedIn: false,
    _t: {},
  },

  onLoad() {
    this._loadI18n()
    this.setData({ isLoggedIn: store.getState().isLoggedIn })
  },

  onShow() {
    const { isLoggedIn } = store.getState()
    if (this.data.isLoggedIn !== isLoggedIn) {
      this.setData({ isLoggedIn })
    }
    this._loadI18n()
  },

  _loadI18n() {
    const features = [
      { id: 'chat', name: i18n.t('aiChat'), icon: '🤖', desc: i18n.t('aiChatDesc'), url: '/pages/ai/chat/index' },
      { id: 'generate', name: i18n.t('aiGenerate'), icon: '✍️', desc: i18n.t('aiGenerateDesc'), url: '/pages/ai/generate/index' },
      { id: 'scan', name: i18n.t('aiScan'), icon: '📸', desc: i18n.t('aiScanDesc'), url: '/pages/ai/scan/index' },
      { id: 'match', name: i18n.t('aiMatch'), icon: '🎯', desc: i18n.t('aiMatchDesc'), url: '/pages/ai/match/index' },
      { id: 'insight', name: i18n.t('aiInsight'), icon: '📊', desc: i18n.t('aiInsightDesc'), url: '/pages/ai/insight/index' },
      { id: 'gaia', name: i18n.t('aiGaia'), icon: '🧠', desc: i18n.t('aiGaiaDesc'), url: '/pages/ai/gaia' },
      { id: 'feedback', name: i18n.t('aiFeedback'), icon: '💬', desc: i18n.t('aiFeedbackDesc'), url: '/pages/ai/feedback' },
      { id: 'config', name: i18n.t('aiConfig'), icon: '⚙️', desc: i18n.t('aiConfigDesc'), url: '/pages/ai/config/index' },
    ]
    this.setData({ features, _t: i18n.getTranslations() })
  },

  go(e) {
    if (!store.checkLogin()) return
    const url = e.currentTarget.dataset.url
    wx.navigateTo({ url })
  },

  goLogin() {
    wx.navigateTo({ url: '/pages/login/index' })
  },

  onShareAppMessage() {
    return { title: i18n.t('aiCenterTitle') + ' - AI数智名片', path: '/pages/ai/index/index' }
  },
})
