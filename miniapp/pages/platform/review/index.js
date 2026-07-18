const { connectionApi } = require('../../../utils/api')

Page({
  data: {
    loading: true,
    activeTab: 'pending',       // 'pending' | 'established'
    pendingList: [],
    establishedList: [],
    pendingCount: 0,
    // 拒绝弹窗
    showRejectModal: false,
    rejectReason: '',
    rejectConnectionId: null,
  },

  onLoad() {
    this.loadPending()
    this.loadEstablished()
  },

  onShow() {
    // 每次显示刷新数据
    this.loadPending()
    this.loadEstablished()
  },

  /** 返回上一页 */
  goBack() {
    wx.navigateBack()
  },

  /** 切换 Tab */
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    if (tab === this.data.activeTab) return
    this.setData({ activeTab: tab })
    if (tab === 'pending') {
      this.loadPending()
    } else {
      this.loadEstablished()
    }
  },

  stopPropagation() {},

  /** 加载待审核列表 — 使用 connectionApi（自动注入 Bearer Token） */
  async loadPending() {
    this.setData({ loading: true })
    try {
      const list = await connectionApi.listPending()
      this.setData({
        pendingList: list || [],
        pendingCount: list?.length || 0,
        loading: false,
      })
    } catch (err) {
      console.error('[Review] 加载待审核列表失败:', err)
      this.setData({
        pendingList: [],
        pendingCount: 0,
        loading: false,
      })
    }
  },

  /** 加载已建联列表 — 使用 connectionApi */
  async loadEstablished() {
    try {
      const list = await connectionApi.list('accepted')
      this.setData({ establishedList: list || [] })
    } catch (err) {
      console.error('[Review] 加载已建联列表失败:', err)
      this.setData({ establishedList: [] })
    }
  },

  /** 批准建联 — 使用 connectionApi */
  async approveConnection(e) {
    const id = e.currentTarget.dataset.id
    if (!id) {
      wx.showToast({ title: '参数错误', icon: 'none' })
      return
    }

    wx.showLoading({ title: '处理中...' })
    try {
      await connectionApi.review(id, true)
      wx.hideLoading()
      wx.showToast({ title: '已批准建联', icon: 'success' })

      // 从列表中移除
      const list = this.data.pendingList.filter(item => item.id !== id)
      this.setData({
        pendingList: list,
        pendingCount: list.length,
      })
      this.loadEstablished()
    } catch (err) {
      wx.hideLoading()
      console.error('[Review] 批准失败:', err)
      wx.showToast({ title: err.message || '网络错误，请重试', icon: 'none' })
    }
  },

  /** 显示拒绝弹窗 */
  showRejectModal(e) {
    const id = e.currentTarget.dataset.id
    this.setData({
      showRejectModal: true,
      rejectReason: '',
      rejectConnectionId: id,
    })
  },

  /** 取消拒绝 */
  cancelReject() {
    this.setData({
      showRejectModal: false,
      rejectReason: '',
      rejectConnectionId: null,
    })
  },

  /** 拒绝原因输入 */
  onRejectReasonInput(e) {
    this.setData({ rejectReason: e.detail.value })
  },

  /** 确认拒绝 — 使用 connectionApi */
  async confirmReject() {
    const { rejectConnectionId, rejectReason } = this.data
    if (!rejectConnectionId) {
      wx.showToast({ title: '参数错误', icon: 'none' })
      return
    }

    wx.showLoading({ title: '处理中...' })
    try {
      await connectionApi.review(rejectConnectionId, false, rejectReason.trim())
      wx.hideLoading()
      this.cancelReject()
      wx.showToast({ title: '已拒绝建联', icon: 'success' })

      // 从列表中移除
      const list = this.data.pendingList.filter(item => item.id !== rejectConnectionId)
      this.setData({
        pendingList: list,
        pendingCount: list.length,
      })
    } catch (err) {
      wx.hideLoading()
      console.error('[Review] 拒绝失败:', err)
      wx.showToast({ title: err.message || '网络错误，请重试', icon: 'none' })
    }
  },
})
