// pages/ai/scan/index.js
const { MockService } = require('../../../utils/mockService')
const HISTORY_KEY = 'scan_history'

Page({
  data: {
    showResult: false,
    loading: false,
    analyzing: false,
    cardData: {
      name: '',
      title: '',
      company: '',
      phone: '',
      email: '',
      address: ''
    },
    scanHistory: [],
    // 识别置信度
    confidence: 0,
    // 原始图片路径（用于保存时提交）
    imagePath: ''
  },

  onLoad() {
    const sys = wx.getSystemInfoSync()
    this.setData({ statusBarHeight: sys.statusBarHeight })
    wx.setNavigationBarTitle({ title: '名片扫描' })
    this.loadHistory()
  },

  onShow() {
    this.loadHistory()
  },

  /** 读取本地扫描历史 */
  loadHistory() {
    try {
      const history = wx.getStorageSync(HISTORY_KEY) || []
      this.setData({ scanHistory: history })
    } catch (e) {
      console.warn('[Scan] 读取扫描历史失败', e)
    }
  },

  /** 保存扫描历史 */
  saveHistory(newItem) {
    try {
      let history = wx.getStorageSync(HISTORY_KEY) || []
      history.unshift(newItem)
      // 最多保留20条
      if (history.length > 20) history = history.slice(0, 20)
      wx.setStorageSync(HISTORY_KEY, history)
      this.setData({ scanHistory: history })
    } catch (e) {
      console.warn('[Scan] 保存扫描历史失败', e)
    }
  },

  /** 选择名片照片并分析 */
  onScan() {
    const that = this
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      success(res) {
        const tempFilePath = res.tempFiles[0].tempFilePath
        that.analyzeCard(tempFilePath)
      },
      fail(err) {
        if (err.errMsg && err.errMsg.indexOf('cancel') === -1) {
          wx.showToast({ title: '选择图片失败', icon: 'none' })
        }
      }
    })
  },

  analyzeCard(imagePath) {
    const that = this
    this.setData({
      loading: true,
      analyzing: true,
      showResult: false,
      cardData: { name: '', title: '', company: '', phone: '', email: '', address: '' },
      imagePath
    })

    wx.showLoading({ title: '识别中...', mask: true })

    MockService.ocrScan(imagePath)
      .then(res => {
        wx.hideLoading()
        const cardInfo = res.data || res
        that.setData({
          loading: false,
          analyzing: false,
          showResult: true,
          cardData: cardInfo,
          confidence: res.confidence || 95
        })
        that.saveHistory({
          name: cardInfo.name || '未知',
          company: cardInfo.company || '',
          time: '刚刚'
        })
      })
      .catch(err => {
        wx.hideLoading()
        that.setData({ loading: false, analyzing: false })
        wx.showToast({ title: '识别失败，请重试', icon: 'none' })
        console.error('[Scan] AI分析失败', err)
      })
  },

  /** 解析AI返回结果，提取名片字段 */
  parseCardResult(data) {
    let parsed = {}
    // 如果返回的是字符串，尝试JSON解析
    if (typeof data === 'string') {
      try {
        // 尝试从文本中提取JSON
        const jsonMatch = data.match(/\{[\s\S]*\}/)
        if (jsonMatch) {
          parsed = JSON.parse(jsonMatch[0])
        }
      } catch (e) {
        console.warn('[Scan] JSON解析失败，使用文本提取', e)
      }
    } else if (typeof data === 'object') {
      parsed = data
      // 如果content字段里有结果
      if (data.content) {
        try {
          const jsonMatch = data.content.match(/\{[\s\S]*\}/)
          if (jsonMatch) parsed = JSON.parse(jsonMatch[0])
        } catch (e) { /* ignore */ }
      }
    }

    return {
      name: parsed.name || parsed.姓名 || '',
      title: parsed.title || parsed.职位 || '',
      company: parsed.company || parsed.公司 || parsed.company_name || '',
      phone: parsed.phone || parsed.手机 || parsed.phone_number || '',
      email: parsed.email || parsed.邮箱 || '',
      address: parsed.address || parsed.地址 || ''
    }
  },

  onSave() {
    const card = this.data.cardData
    if (!card.name && !card.company) {
      wx.showToast({ title: '识别信息不完整', icon: 'none' })
      return
    }

    wx.showLoading({ title: '保存中...', mask: true })

    const contactLines = []
    if (card.name) contactLines.push(`姓名：${card.name}`)
    if (card.title) contactLines.push(`职位：${card.title}`)
    if (card.company) contactLines.push(`公司：${card.company}`)
    if (card.phone) contactLines.push(`电话：${card.phone}`)
    if (card.email) contactLines.push(`邮箱：${card.email}`)
    if (card.address) contactLines.push(`地址：${card.address}`)

    const brochureData = {
      title: card.name || '未命名名片',
      cover: this.data.imagePath || '',
      purpose: 'partner',
      pages: [{
        content_type: 'cover',
        sort_order: 0,
        content: contactLines.join('\n'),
        image_url: this.data.imagePath || '',
      }],
      ...card
    }

    MockService.createBrochure(brochureData)
      .then(res => {
        wx.hideLoading()
        wx.showToast({ title: '已保存到名片夹', icon: 'success', duration: 1500 })

        setTimeout(() => {
          wx.redirectTo({
            url: `/pages/brochure/preview/index?id=${res.id}`,
          })
        }, 1500)

        this.setData({
          showResult: false,
          imagePath: '',
          cardData: { name: '', title: '', company: '', phone: '', email: '', address: '' }
        })
      })
      .catch(err => {
        wx.hideLoading()
        wx.showToast({ title: '保存失败，请重试', icon: 'none' })
        console.error('[Scan] 保存名片失败', err)
      })
  },

  /** 重新扫描 */
  onRetry() {
    this.setData({
      showResult: false,
      cardData: { name: '', title: '', company: '', phone: '', email: '', address: '' },
      imagePath: ''
    })
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
