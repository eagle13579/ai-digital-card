const MockService = require('../../../utils/mockService')

const MOCK_RESULT = {
  name: '张三',
  title: '产品经理',
  company: '星辰科技有限公司',
  phone: '13800138000',
  email: 'zhangsan@example.com',
  address: '北京市海淀区中关村大街1号',
}

/**
 * 解析扫码结果协议
 * xunfu://user/{id} → 跳转用户名片
 * xunfu://platform/{id} → 跳转平台详情
 * xunfu://resource/{id} → 跳转资源详情
 * 其他 → 视为文本搜索
 */
function parseScanResult(raw) {
  const patterns = {
    user: /^xunfu:\/\/user\/(.+)/,
    platform: /^xunfu:\/\/platform\/(.+)/,
    resource: /^xunfu:\/\/resource\/(.+)/,
    bizcard: /^bizcard:\/\/user\/(.+)/,
  }
  for (const [type, pattern] of Object.entries(patterns)) {
    const match = raw.match(pattern)
    if (match) {
      return { type, id: match[1], raw }
    }
  }
  // 尝试匹配通用链接格式
  const urlMatch = raw.match(/https?:\/\/[^/]+\/([a-z]+\/(\S+))/)
  if (urlMatch) {
    const parts = urlMatch[1].split('/')
    if (parts.length >= 2) {
      return { type: parts[0], id: parts[1], raw }
    }
  }
  return null
}

Page({
  data: {
    imagePath: '',
    scanning: false,
    result: null,
    showResult: false,
    scanCount: 0,
    maxScans: 3,
    // 扫码模式
    scanMode: 'ocr', // ocr | qrcode
    qrResult: null,
    showQrResult: false,
  },

  onLoad() {
    this.loadScanCount()
  },

  loadScanCount() {
    const scanCount = wx.getStorageSync('scanCount') || 0
    this.setData({ scanCount })
  },

  checkLoginAndLimit() {
    const store = require('../../utils/store')
    const state = store.getState()
    if (!state.token) {
      getApp().checkLogin()
      return false
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
      return false
    }
    return true
  },

  // ====== OCR名片识别（原有） ======
  takePhoto() {
    if (!this.checkLoginAndLimit()) return

    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const imagePath = res.tempFilePaths[0]
        this.setData({ imagePath, scanning: true, scanMode: 'ocr' })
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

  // ====== 二维码扫码 ======
  scanQRCode() {
    if (!this.checkLoginAndLimit()) return

    wx.scanCode({
      onlyFromCamera: false,
      scanType: ['qrCode', 'barCode'],
      success: (res) => {
        const raw = res.result
        const parsed = parseScanResult(raw)

        if (parsed) {
          this.handleScanProtocol(parsed)
        } else {
          // 无协议前缀，视为普通文本
          this.setData({
            scanMode: 'qrcode',
            qrResult: { raw, type: 'text', id: raw },
            showQrResult: true,
            scanCount: this.data.scanCount + 1,
          })
          wx.setStorageSync('scanCount', this.data.scanCount + 1)
        }
      },
      fail: (err) => {
        console.error('[Scan] 扫码失败:', err)
        wx.showToast({ title: '扫码失败', icon: 'none' })
      },
    })
  },

  /**
   * 处理扫码协议跳转
   */
  handleScanProtocol(parsed) {
    const { type, id } = parsed
    wx.showToast({ title: `识别到${type}`, icon: 'success' })

    // 更新扫码计数
    this.setData({ scanCount: this.data.scanCount + 1 })
    wx.setStorageSync('scanCount', this.data.scanCount + 1)

    // 延迟跳转，让用户看到提示
    setTimeout(() => {
      switch (type) {
        case 'user':
        case 'bizcard':
          wx.navigateTo({ url: `/pages/card/card?id=${id}` })
          break
        case 'platform':
          wx.navigateTo({ url: `/pages/platform/manage/index?id=${id}` })
          break
        case 'resource':
          wx.navigateTo({ url: `/pages/brochure/preview/index?id=${id}` })
          break
        default:
          // 文本搜索
          wx.navigateTo({
            url: `/pages/ai/match/index?keyword=${encodeURIComponent(id)}`,
          })
      }
    }, 800)
  },

  // ====== 结果处理 ======
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
      qrResult: null,
      showQrResult: false,
    })
  },

  editField(e) {
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    if (this.data.result) {
      this.setData({ [`result.${field}`]: value })
    }
  },

  // 跳转到文本搜索结果
  searchText() {
    const keyword = this.data.qrResult?.id
    if (keyword) {
      wx.navigateTo({
        url: `/pages/ai/match/index?keyword=${encodeURIComponent(keyword)}`,
      })
    }
  },
})
