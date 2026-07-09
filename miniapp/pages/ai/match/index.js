// pages/ai/match/index.js
const { MockService } = require('../../../utils/mockService')

Page({
  data: {
    loading: true,
    refreshing: false,
    error: false,
    errorMsg: '',
    empty: false,

    preferences: {
      industry: 'tech',
      region: 'bj',
      position: 'manager'
    },

    recommendations: [],

    // 连接中状态
    connectingId: null
  },

  onLoad() {
    const sys = wx.getSystemInfoSync()
    this.setData({ statusBarHeight: sys.statusBarHeight })
    wx.setNavigationBarTitle({ title: '人脉匹配' })
    this.loadRecommendations()
  },

  loadRecommendations() {
    this.setData({ loading: true, error: false, errorMsg: '', empty: false })

    MockService.getRecommendations({
      industry: this.data.preferences.industry,
      region: this.data.preferences.region,
      position: this.data.preferences.position,
      limit: 20
    })
      .then(res => {
        const list = res.list || res.data || res.recommendations || res.items || []
        const normalized = list.map((item, index) => ({
          id: item.id || item.user_id || index,
          avatar: item.avatar || item.avatar_url || '',
          name: item.name || item.nickname || item.username || '未知',
          title: item.title || item.position || item.job_title || '',
          company: item.company || item.company_name || '',
          matchScore: item.matchScore || item.match_score || item.score || 0,
          tags: item.tags || item.interests || item.skills || [],
          connected: item.connected || item.is_connected || false
        }))

        this.setData({
          loading: false,
          refreshing: false,
          recommendations: normalized,
          empty: normalized.length === 0
        })
      })
      .catch(err => {
        console.error('[Match] 获取推荐失败', err)
        this.setData({
          loading: false,
          refreshing: false,
          error: true,
          errorMsg: err.errMsg || err.message || '获取推荐列表失败'
        })
      })
  },

  /** 下拉刷新 */
  onPullDownRefresh() {
    this.setData({ refreshing: true })
    this.loadRecommendations()
    wx.stopPullDownRefresh()
  },

  /** 偏好变更 */
  onPreferenceChange(e) {
    const dataset = e.currentTarget.dataset
    const type = dataset.type || ''
    const value = dataset.value || ''

    if (!type || !value) return

    const key = `preferences.${type}`
    this.setData({ [key]: value }, () => {
      wx.showToast({ title: '偏好已更新', icon: 'none' })
      // 重新加载推荐
      this.loadRecommendations()
    })
  },

  onConnect(e) {
    const id = e.currentTarget.dataset.id
    if (!id) return

    const item = this.data.recommendations.find(r => r.id === id)
    if (item && item.connected) {
      wx.showToast({ title: '已是好友', icon: 'none' })
      return
    }

    this.setData({ connectingId: id })
    wx.showLoading({ title: '请求中...', mask: true })

    MockService.unlockContact(id)
      .then(res => {
        wx.hideLoading()
        wx.showToast({ title: '名片交换请求已发送', icon: 'success' })

        const list = this.data.recommendations.map(r => {
          if (r.id === id) r.connected = true
          return r
        })
        this.setData({
          recommendations: list,
          connectingId: null
        })
      })
      .catch(err => {
        wx.hideLoading()
        this.setData({ connectingId: null })
        wx.showToast({ title: err.errMsg || '请求失败', icon: 'none' })
        console.error('[Match] 交换名片失败', err)
      })
  },

  /** 在线沟通 */
  onChat(e) {
    const id = e.currentTarget.dataset.id
    // 先检查是否已交换名片
    const item = this.data.recommendations.find(r => r.id === id)
    if (item && !item.connected) {
      wx.showToast({ title: '请先交换名片', icon: 'none' })
      return
    }
    wx.navigateTo({
      url: `/pages/ai/chat/index?targetId=${id}`
    })
  },

  /** 重试加载 */
  onRetry() {
    this.loadRecommendations()
  },

  goBack() {
    wx.navigateBack({
      delta: 1,
      fail: () => {
        wx.switchTab({ url: '/pages/index/index' })
      }
    })
  }
})
