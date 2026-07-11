/**
 * AI配置
 */
Page({
  data: { autoMatch: true, smartReply: false, dataSync: true, dailyDigest: false },
  toggle(e) {
    const key = e.currentTarget.dataset.key
    this.setData({ [key]: !this.data[key] })
    wx.showToast({ title: '已更新', icon: 'success' })
  },
})
