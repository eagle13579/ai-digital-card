// pages/ai/config/index.js
const { MockService } = require('../../../utils/mockService')

Page({
  data: {
    loading: true,
    saving: false,
    settings: {
      autoReply: true,
      smartRecommend: true,
      dataAnalysis: false,
      filterSensitive: true,
      timeout: 30,
      welcomeMessage: '您好！我是AI智能客服，请问有什么可以帮您的？'
    }
  },

  onLoad() {
    const sys = wx.getSystemInfoSync()
    this.setData({ statusBarHeight: sys.statusBarHeight })
    wx.setNavigationBarTitle({ title: '客服配置' })
    this.loadConfig()
  },

  async loadConfig() {
    this.setData({ loading: true })
    try {
      const config = await MockService.getAIConfig()
      if (config && Object.keys(config).length > 0) {
        this.setData({
          settings: {
            autoReply: config.autoReply !== undefined ? config.autoReply : true,
            smartRecommend: config.smartRecommend !== undefined ? config.smartRecommend : true,
            dataAnalysis: config.dataAnalysis !== undefined ? config.dataAnalysis : false,
            filterSensitive: config.filterSensitive !== undefined ? config.filterSensitive : true,
            timeout: config.timeout !== undefined ? config.timeout : 30,
            welcomeMessage: config.welcomeMessage || '您好！我是AI智能客服，请问有什么可以帮您的？'
          }
        })
      }
    } catch (err) {
      console.warn('[AIConfig] 加载配置失败，使用默认值', err)
    } finally {
      this.setData({ loading: false })
    }
  },

  onToggle(e) {
    const key = e.currentTarget.dataset.key
    const value = e.detail.value
    this.setData({
      [`settings.${key}`]: value
    })
  },

  onWelcomeInput(e) {
    this.setData({
      'settings.welcomeMessage': e.detail.value
    })
  },

  async onSave() {
    this.setData({ saving: true })
    wx.showLoading({ title: '保存中...' })

    try {
      const data = {
        autoReply: this.data.settings.autoReply,
        smartRecommend: this.data.settings.smartRecommend,
        dataAnalysis: this.data.settings.dataAnalysis,
        filterSensitive: this.data.settings.filterSensitive,
        timeout: this.data.settings.timeout,
        welcomeMessage: this.data.settings.welcomeMessage,
      }
      await MockService.saveAIConfig(data)
      wx.hideLoading()
      wx.showToast({ title: '配置已保存', icon: 'success' })
    } catch (err) {
      wx.hideLoading()
      console.error('[AIConfig] 保存失败', err)
      wx.showToast({ title: '保存失败，请重试', icon: 'none' })
    } finally {
      this.setData({ saving: false })
    }
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
