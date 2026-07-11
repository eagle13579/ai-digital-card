const MockService = require('../../utils/mockService')

Page({
  data: { 
    brochure: null, 
    qrcodeData: '',
    generating: false,
  },

  async onLoad(options) {
    const id = options.id || ''
    const brochure = id ? await MockService.getBrochureById(id) : null
    
    if (!brochure) {
      wx.showToast({ title: '请先创建名片', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
      return
    }

    this.setData({ 
      brochure, 
      qrcodeData: 'https://card.example.com/brochure/' + brochure.id 
    })
    this.generateQRCode()
  },

  generateQRCode() {
    if (this.data.generating) return
    this.setData({ generating: true })

    setTimeout(() => {
      this.setData({ generating: false })
      wx.showToast({ title: '二维码已就绪', icon: 'success' })
    }, 800)
  },

  saveQR() {
    wx.showToast({ title: '长按图片保存', icon: 'none' })
  },

  onShareAppMessage() {
    const b = this.data.brochure
    return { 
      title: (b && b.title) || '名片二维码', 
      path: '/pages/qrcode/index?id=' + ((b && b.id) || ''),
      imageUrl: (b && b.cover) || '',
    }
  },

  onShareTimeline() {
    const b = this.data.brochure
    return { title: (b && b.title) || '名片二维码' }
  },
})
