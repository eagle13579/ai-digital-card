// pages/ai/scan/index.js — AI名片扫描分析 (真实API连接)
// 功能：拍照/选图 → 后端AI分析识别名片信息 → 确认保存到名片夹

const { aiApi, brochureApi } = require('../../../utils/api')

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

  /** 调用后端AI分析名片图片 */
  analyzeCard(imagePath) {
    const that = this
    this.setData({
      loading: true,
      analyzing: true,
      showResult: false,
      cardData: { name: '', title: '', company: '', phone: '', email: '', address: '' },
      imagePath
    })

    // 先显示识别中的loading
    wx.showLoading({ title: '识别中...', mask: true })

    // 调用后端 AI assist/write 接口，传图片描述分析名片
    // 由于小程序不能直接传二进制给AI接口，用base64或描述方式
    // 实际场景：先用wx.getFileSystemManager读取为base64，或直接上传图片
    // 这里使用wx.getImageInfo获取图片后，调用aiApi.getChat进行OCR识别
    const fm = wx.getFileSystemManager()
    fm.readFile({
      filePath: imagePath,
      encoding: 'base64',
      success(fileRes) {
        const base64Data = fileRes.data
        // 通过AI对话接口传图片base64，让后端做OCR识别
        aiApi.getChat({
          messages: [
            { role: 'system', content: '你是一个名片OCR识别专家。请识别图片中的名片信息，提取姓名(name)、职位(title)、公司(company)、手机号(phone)、邮箱(email)、地址(address)。只返回JSON格式，不要其他文字。' },
            { role: 'user', content: '请识别这张名片上的信息。', image_base64: base64Data, image_mime: 'image/jpeg' }
          ]
        })
          .then(res => {
            wx.hideLoading()
            const data = res.data || res
            const cardInfo = that.parseCardResult(data)
            that.setData({
              loading: false,
              analyzing: false,
              showResult: true,
              cardData: cardInfo
            })
          })
          .catch(err => {
            wx.hideLoading()
            that.setData({ loading: false, analyzing: false })
            wx.showToast({ title: '识别失败，请重试', icon: 'none' })
            console.error('[Scan] AI分析失败', err)
          })
      },
      fail(err) {
        wx.hideLoading()
        that.setData({ loading: false, analyzing: false })
        wx.showToast({ title: '读取图片失败', icon: 'none' })
        console.error('[Scan] 读取图片失败', err)
      }
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

  /** 确认保存到名片夹 */
  onSave() {
    const card = this.data.cardData
    if (!card.name && !card.company) {
      wx.showToast({ title: '识别信息不完整', icon: 'none' })
      return
    }

    wx.showLoading({ title: '保存中...', mask: true })

    // 构建后端期望的字段映射
    const brochureData = {
      title: card.name || '未命名名片',
      cover: this.data.imagePath || '',
      purpose: '从OCR扫描创建',
      pages: [{
        type: 'contact',
        name: card.name || '',
        title: card.title || '',
        company: card.company || '',
        phone: card.phone || '',
        email: card.email || '',
        address: card.address || ''
      }]
    }

    brochureApi.create(brochureData)
      .then(res => {
        wx.hideLoading()
        wx.showToast({ title: '已保存到名片夹', icon: 'success', duration: 1500 })

        // 记录扫描历史
        this.saveHistory({
          name: card.name || '未知',
          company: card.company || '',
          time: '刚刚'
        })

        // 跳转到预览页
        setTimeout(() => {
          wx.redirectTo({
            url: `/pages/brochure/preview/index?id=${res.id}`,
          })
        }, 1500)

        // 重置，准备下一次扫描
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
