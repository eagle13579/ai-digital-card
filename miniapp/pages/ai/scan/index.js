const MockService = require('../../../utils/mockService')

const MOCK_RESULT = {
  name: '张三',
  title: '产品经理',
  company: '星辰科技有限公司',
  phone: '13800138000',
  email: 'zhangsan@example.com',
  address: '北京市海淀区中关村大街1号',
}

Page({
  data: {
    imagePath: '',
    scanning: false,
    result: null,
    showResult: false,
    scanCount: 0,
    maxScans: 3,
  },

  onLoad() {
    this.loadScanCount()
  },

  loadScanCount() {
    const scanCount = wx.getStorageSync('scanCount') || 0
    this.setData({ scanCount })
  },

  takePhoto() {
    const app = getApp()
    if (!app.isLoggedIn()) {
      return wx.showToast({ title: '请先登录', icon: 'none' })
    }

    if (this.data.scanCount >= this.data.maxScans) {
      wx.showModal({
        title: '扫描次数已用完',
        content: '升级到Pro会员可享受更多扫描次数',
        confirmText: '去升级',
        confirmColor: '#8b5cf6',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/membership/index' })
          }
        },
      })
      return
    }

    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const imagePath = res.tempFilePaths[0]
        this.setData({ imagePath, scanning: true })
        this.scanImage(imagePath)
      },
      fail: () => {
        wx.showToast({ title: '请选择图片', icon: 'none' })
      },
    })
  },

  scanImage(imagePath) {
    setTimeout(() => {
      const result = { ...MOCK_RESULT }
      this.setData({
        scanning: false,
        result,
        showResult: true,
        scanCount: this.data.scanCount + 1,
      })
      wx.setStorageSync('scanCount', this.data.scanCount + 1)
      wx.showToast({ title: '识别成功', icon: 'success' })
    }, 1500)
  },

  saveCard() {
    const result = this.data.result
    if (!result) return

    wx.showLoading({ title: '保存中...' })
    setTimeout(() => {
      wx.hideLoading()
      wx.showToast({ title: '已保存到名片', icon: 'success' })
      setTimeout(() => {
        wx.navigateTo({ url: '/pages/brochure/preview/index' })
      }, 1500)
    }, 800)
  },

  reScan() {
    this.setData({
      imagePath: '',
      result: null,
      showResult: false,
    })
  },

  editField(e) {
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    if (this.data.result) {
      this.setData({ [`result.${field}`]: value })
    }
  },
})