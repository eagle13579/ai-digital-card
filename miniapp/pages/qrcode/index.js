const MockService = require('../../utils/mockService')

Page({
  data: { 
    brochure: null, 
    qrcodeData: '',
    retryCount: 0,
    maxRetries: 2,
    generating: false,
  },

  onLoad(options) {
    const id = options.id || ''
    const brochure = MockService.getBrochureById(id)
    this.setData({ brochure, qrcodeData: 'https://card.example.com/brochure/' + ((brochure && brochure.id) || '') })
    this.generateQRCode()
  },

  generateQRCode() {
    if (this.data.generating || this.data.retryCount >= this.data.maxRetries) {
      if (this.data.retryCount >= this.data.maxRetries) {
        wx.showToast({ title: '二维码生成失败', icon: 'error' })
      }
      return
    }

    this.setData({ generating: true, retryCount: this.data.retryCount + 1 })

    setTimeout(() => {
      const success = true // 移除随机失败逻辑
      if (success) {
        this.setData({ generating: false })
        wx.showToast({ title: '二维码生成成功', icon: 'success' })
      } else {
        this.setData({ generating: false })
        this.fallbackQRCode()
      }
    }, 800)
  },

  fallbackQRCode() {
    if (this.data.retryCount >= this.data.maxRetries) {
      wx.showToast({ title: '二维码生成失败，请稍后重试', icon: 'none' })
      return
    }
    this.generateQRCode()
  },

  saveQR() {
    wx.showToast({ title: '长按图片保存', icon: 'none' })
  },

  onShareAppMessage() {
    const brochure = this.data.brochure
    return { 
      title: (brochure && brochure.title) || '名片二维码', 
      path: '/pages/qrcode/index?id=' + ((brochure && brochure.id) || ''),
      imageUrl: (brochure && brochure.cover) || '',
    }
  },

  onShareTimeline() {
    const brochure = this.data.brochure
    return {
      title: (brochure && brochure.title) || '名片二维码',
    }
  },
})