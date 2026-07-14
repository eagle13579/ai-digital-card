/**
 * AI配置
 */
Page({
  data: { autoMatch: true, smartReply: false, dataSync: true, dailyDigest: false, useRealApi: true },
  toggle(e) {
    const key = e.currentTarget.dataset.key
    this.setData({ [key]: !this.data[key] })
    wx.setStorageSync('ai_config', this.data)
    wx.showToast({ title: '已更新', icon: 'success' })
  },
  onLoad() {
    const saved = wx.getStorageSync('ai_config')
    if (saved) this.setData({ ...saved })
  },
})
