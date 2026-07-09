/**
 * pages/ai/generate/index.js
 * AI内容生成页面 — 输入提示词 => 调用API生成内容 => 展示结果 => 历史记录
 * 后端 API: POST /api/v1/ai/assist/generate
 * 使用 aiApi.generate() — 支持 write / summary / rewrite 三种模式
 * Mock模式: USE_MOCK=true 走 MockService 伪数据（便于测试），设为 false 即连接真实API
 */
const { MockService } = require('../../../utils/mockService')

const TAB_MODES = ['write', 'summary', 'rewrite']

Page({
  data: {
    currentTab: 0,
    prompt: '',
    isGenerating: false,
    resultContent: '',
    /** 是否使用 DeepSeek 深度生成模式 */
    useDeepSeek: false,
    templates: [
      { id: 1, title: '产品介绍', desc: '生成产品发布文案', mode: 'write' },
      { id: 2, title: '个人简介', desc: '专业自我介绍', mode: 'write' },
      { id: 3, title: '新闻通稿', desc: '快速撰写新闻稿', mode: 'write' },
      { id: 4, title: '社交媒体', desc: '社交平台发文', mode: 'write' },
      { id: 5, title: '文章摘要', desc: '提炼核心内容', mode: 'summary' },
      { id: 6, title: '文案润色', desc: '优化表达方式', mode: 'rewrite' },
    ],
    history: [],
  },

  onLoad() {
    const sys = wx.getSystemInfoSync()
    this.setData({ statusBarHeight: sys.statusBarHeight })
    this.loadHistory()
  },

  // ===== 页面交互 =====

  goBack() {
    wx.navigateBack({ delta: 1 })
  },

  switchTab(e) {
    const tab = parseInt(e.currentTarget.dataset.tab)
    this.setData({ currentTab: tab, resultContent: '' })
  },

  /** 切换 AI 生成模式: 标准模式 ↔ DeepSeek 深度生成 */
  switchDeepSeek() {
    this.setData({ useDeepSeek: !this.data.useDeepSeek, resultContent: '' })
  },

  onSelectTemplate(e) {
    const template = e.currentTarget.dataset.template
    this.setData({ prompt: template.title + ' — ' })
    // 自动切换到对应模式
    const modeIndex = TAB_MODES.indexOf(template.mode)
    if (modeIndex >= 0 && modeIndex !== this.data.currentTab) {
      this.setData({ currentTab: modeIndex, resultContent: '' })
    }
  },

  // ===== AI 生成 =====

  onGenerate() {
    const { prompt, isGenerating, useDeepSeek } = this.data
    if (!prompt.trim() || isGenerating) return

    this.setData({ isGenerating: true, resultContent: '' })

    const mode = TAB_MODES[this.data.currentTab]

    wx.showLoading({ title: useDeepSeek ? 'DeepSeek生成中...' : 'AI生成中...' })

    MockService.aiGenerate(prompt.trim(), mode, useDeepSeek)
      .then((res) => {
        const content = res.content || ''
        this.setData({ resultContent: content })
        if (content) {
          this.saveToHistory(prompt.trim(), content)
          wx.showToast({ title: '生成完成', icon: 'success' })
        }
      })
      .catch((err) => {
        console.error('[AI生成] 请求失败:', err)
        wx.showToast({ title: '请求失败，请重试', icon: 'none' })
      })
      .finally(() => {
        wx.hideLoading()
        this.setData({ isGenerating: false })
      })
  },

  // ===== 结果操作 =====

  onCopy() {
    if (!this.data.resultContent) return
    wx.setClipboardData({
      data: this.data.resultContent,
      success: () => {
        wx.showToast({ title: '已复制到剪贴板', icon: 'success' })
      },
    })
  },

  onReuse() {
    // 重新生成
    this.onGenerate()
  },

  // ===== 历史记录 =====

  saveToHistory(prompt, result) {
    const item = {
      id: Date.now(),
      prompt: prompt.length > 30 ? prompt.substring(0, 30) + '...' : prompt,
      result,
      mode: TAB_MODES[this.data.currentTab],
      time: new Date().toLocaleString('zh-CN'),
    }

    let history = wx.getStorageSync('ai_generate_history') || []
    history.unshift(item)
    if (history.length > 20) history = history.slice(0, 20)
    wx.setStorageSync('ai_generate_history', history)
    this.setData({ history })
  },

  loadHistory() {
    const history = wx.getStorageSync('ai_generate_history') || []
    this.setData({ history })
  },

  // ===== 分享 =====

  onShareAppMessage() {
    return {
      title: 'AI 内容生成 — 智能创作助手',
      path: '/pages/ai/generate/index',
    }
  },
})
