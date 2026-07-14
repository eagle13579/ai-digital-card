/**
 * 我的 - 个人中心/会员信息/设置 (i18n enabled)
 */
const { MockService } = require('../../utils/mockService')
const i18n = require('../../utils/i18n')
const store = require('../../utils/store')

Page({
  data: {
    loading: true,
    userInfo: {},
    memberLevel: 'free',
    memberLevelText: 'Free',
    memberExpire: '',
    trustCount: 0,
    newVisitorCount: 0,
    stats: { visitors: 0, matches: 0, unlocks: 0, views: 0 },
    // 注销账号弹窗
    showDeleteModal: false,
    deleteConfirmText: '',
    // i18n
    _t: {},
  },

  onLoad() {
    // 登录守卫：未登录立即跳登录页
    const { isLoggedIn } = store.getState()
    if (!isLoggedIn) {
      wx.redirectTo({ url: '/pages/login/index' })
      return
    }
    this._loadI18n()
    this.loadProfile()
  },

  onShow() {
    if (!this.data.loading) {
      this.loadProfile()
    }
    this._loadI18n()
  },

  /** 加载国际化翻译 */
  _loadI18n() {
    this.setData({ _t: i18n.getTranslations() })
  },

  async loadProfile() {
    this.setData({ loading: true })
    try {
      const [profile, brochures, trustNet, visitorStats] = await Promise.all([
        MockService.getProfile(),
        MockService.getBrochures(),
        MockService.getTrustNetwork(),
        MockService.getVisitorStats(),
      ])

      const brochureList = Array.isArray(brochures) ? brochures : (brochures.data || [])
      const brochure = brochureList[0]

      const { getLevelText } = require('../../utils/levels')
      const memberLevel = profile.member_level || 'free'
      const memberLevelText = getLevelText(memberLevel)

      let stats = { visitors: visitorStats.total_visits || 0, matches: 0, unlocks: 0, views: visitorStats.view_count || 0 }
      const newVisitorCount = visitorStats.new_visitors || visitorStats.todayVisits || 0

      const trustCount = (trustNet.trusting || []).length

      this.setData({
        userInfo: {
          id: profile.id,
          name: profile.name || '',
          avatar: profile.avatar || '',
          company: profile.company || '',
          title: profile.title || '',
        },
        memberLevel,
        memberLevelText,
        memberExpire: profile.member_expire || '',
        trustCount,
        newVisitorCount,
        stats,
        loading: false,
      })

      store.updateUserInfo(this.data.userInfo)
      store.updateMemberLevel(memberLevel)
    } catch (err) {
      console.error('加载个人数据失败:', err)
      this.setData({ loading: false })
    }
  },

  // ── 语言切换 ────────────────────────────────────────────────

  /** 切换语言：中文 ↔ English */
  switchLanguage() {
    const current = i18n.getLocale()
    const next = current === 'zh' ? 'en' : 'zh'
    i18n.setLocale(next)
    store.setLocale(next)
    // 刷新当前页面翻译
    this._loadI18n()
    wx.showToast({
      title: next === 'zh' ? '已切换至中文' : 'Switched to English',
      icon: 'none',
      duration: 1500,
    })
  },

  // 编辑名片
  goEditCard() {
    wx.navigateTo({ url: '/pages/brochure/create/index' })
  },

  // 画册管理
  goAlbum() {
    wx.navigateTo({ url: '/pages/brochure/create/index' })
  },

  // 会员中心
  goMember() {
    wx.navigateTo({ url: '/pages/membership/index' })
  },

  // 访客记录
  goVisitorLog() {
    wx.showToast({ title: i18n.t('featureInDev'), icon: 'none' })
  },

  // 信任网络
  goTrustNetwork() {
    wx.navigateTo({ url: '/pages/network/graph/index' })
  },

  // AI智能中心
  goAICenter() {
    wx.navigateTo({ url: '/pages/ai/index/index' })
  },

  // 隐私设置
  goPrivacy() {
    wx.navigateTo({ url: '/pages/agreement/privacy/index' })
  },

  // 关于
  goAbout() {
    wx.showToast({ title: i18n.t('versionInfo'), icon: 'none' })
  },

  // ── 注销账号 ────────────────────────────────────────────────────

  /** 点击"注销账号"链接 — 先弹出警告确认 */
  showDeleteConfirm() {
    wx.showModal({
      title: i18n.t('deleteTitle'),
      content: i18n.t('deleteConfirmContent'),
      confirmText: i18n.t('deleteConfirmAction'),
      confirmColor: '#ef4444',
      success: (res) => {
        if (res.confirm) {
          // 用户确认警告后，弹出输入确认框
          this.setData({ showDeleteModal: true, deleteConfirmText: '' })
        }
      },
    })
  },

  /** 隐藏注销确认弹窗 */
  hideDeleteConfirm() {
    this.setData({ showDeleteModal: false, deleteConfirmText: '' })
  },

  /** 输入框内容变化 */
  onDeleteInput(e) {
    this.setData({ deleteConfirmText: e.detail.value })
  },

  /** 确认注销（输入验证通过后调用） */
  async confirmDeleteAccount() {
    if (this.data.deleteConfirmText !== '确认注销') {
      return
    }

    // 防止重复点击
    wx.showLoading({ title: i18n.t('deactivating'), mask: true })

    try {
      const { authApi } = require('../../utils/api')
      await authApi.deleteAccount()

      wx.hideLoading()

      // 清除本地登录态
      const app = getApp()
      app.clearLogin()

      wx.showToast({ title: i18n.t('accountDeleted'), icon: 'success', duration: 2000 })
      setTimeout(() => {
        wx.reLaunch({ url: '/pages/index/index' })
      }, 2000)
    } catch (err) {
      wx.hideLoading()
      console.error('注销账号失败:', err)
    } finally {
      this.setData({ showDeleteModal: false, deleteConfirmText: '' })
    }
  },

  /** 空处理函数 — 阻止弹窗点击穿透 */
  noop() {
    // nothing
  },

  // 退出登录
  logout() {
    wx.showModal({
      title: i18n.t('logoutTitle'),
      content: i18n.t('logoutContent'),
      success: (res) => {
        if (res.confirm) {
          const app = getApp()
          app.clearLogin()
          wx.reLaunch({ url: '/pages/index/index' })
        }
      },
    })
  },
})
