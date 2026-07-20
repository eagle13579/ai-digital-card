/**
 * 连接管理 — 我的连接 + 待审核请求
 * 迁移自 liankebao-weapp (Taro React → 原生微信)
 */
const { connectionApi } = require('../../utils/api')

Page({
  data: {
    activeTab: 'connections',
    status: 'loading',
    errorMsg: '',
    connections: [],
    connectionsLoaded: false,
    pendingList: [],
    pendingLoaded: false,
  },

  onLoad() {
    this.loadAll()
  },

  onShow() {
    if (this.data.status === 'ready') {
      this.loadAll()
    }
  },

  /** 切换Tab */
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ activeTab: tab })
  },

  /** 加载连接列表 */
  async loadConnections() {
    try {
      const res = await connectionApi.list('approved')
      const list = res.data || res || []
      this.setData({
        connections: Array.isArray(list) ? list : [],
        connectionsLoaded: true,
      })
    } catch {
      this.setData({ connections: [], connectionsLoaded: true })
    }
  },

  /** 加载待审核列表 */
  async loadPending() {
    try {
      const res = await connectionApi.listPending()
      const list = res.data || res || []
      this.setData({
        pendingList: Array.isArray(list) ? list : [],
        pendingLoaded: true,
      })
    } catch {
      this.setData({ pendingList: [], pendingLoaded: true })
    }
  },

  /** 加载全部 */
  async loadAll() {
    this.setData({ status: 'loading', errorMsg: '' })
    try {
      await Promise.all([this.loadConnections(), this.loadPending()])
      this.setData({ status: 'ready' })
    } catch {
      this.setData({
        status: 'error',
        errorMsg: '加载失败，请检查网络后重试',
      })
    }
  },

  /** 批准 */
  async handleApprove(e) {
    const id = e.currentTarget.dataset.id
    wx.showLoading({ title: '正在批准...' })
    try {
      const res = await connectionApi.review(id, true)
      wx.hideLoading()
      if (res.code === 200 || res.code === 0) {
        wx.showToast({ title: '已建立连接', icon: 'success' })
        this.loadPending()
        this.loadConnections()
      } else {
        wx.showToast({ title: res.message || '操作失败', icon: 'none' })
      }
    } catch {
      wx.hideLoading()
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  /** 拒绝 */
  async handleReject(e) {
    const id = e.currentTarget.dataset.id
    wx.showLoading({ title: '正在拒绝...' })
    try {
      const res = await connectionApi.review(id, false)
      wx.hideLoading()
      if (res.code === 200 || res.code === 0) {
        wx.showToast({ title: '已拒绝', icon: 'success' })
        this.loadPending()
      } else {
        wx.showToast({ title: res.message || '操作失败', icon: 'none' })
      }
    } catch {
      wx.hideLoading()
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  /** 跳转用户名片 */
  goToCardDetail(e) {
    const userId = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/card/card?userId=${userId}` })
  },

  goToUserDetail(e) {
    const userId = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/card/card?userId=${userId}` })
  },

  /** 跳转匹配页 */
  goToMatch() {
    wx.switchTab({ url: '/pages/index/index' })
  },
})
