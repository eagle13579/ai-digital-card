const { MockService } = require('../../../utils/mockService')
const { aiApi } = require('../../../utils/api')
const store = require('../../../utils/store')
const i18nMixin = require('../../../utils/i18n-mixin')
const CHAT_STORAGE_KEY = 'ai_chat_messages'
const MAX_MESSAGES = 200 // 最大保留消息数

Page(i18nMixin.attach({
  data: {
    messages: [],
    inputValue: '',
    loading: false,
    userAvatar: '',
    canSend: false,
    isLoggedIn: false,
  },

  async onLoad() {
    // 恢复聊天记录
    try {
      const saved = wx.getStorageSync(CHAT_STORAGE_KEY)
      if (saved && saved.length > 0) {
        // 限制最大消息数，超出时保留最新 MAX_MESSAGES 条
        const trimmed = saved.length > MAX_MESSAGES ? saved.slice(-MAX_MESSAGES) : saved
        this.setData({ messages: trimmed })
      } else {
        this.setData({
          messages: [{role:'ai', content: i18nMixin.t('aiChatDefaultGreeting')}]
        })
      }
    } catch (e) {
      this.setData({
        messages: [{role:'ai', content: i18nMixin.t('aiChatDefaultGreeting')}]
      })
    }

    const app = getApp()
    const isLoggedIn = store.getState().isLoggedIn

    if (isLoggedIn) {
      try {
        const res = await MockService.getUserProfile()
        const profile = res?.data || {}
        const userAvatar = profile.avatar || ''
        this.setData({ userAvatar, isLoggedIn })
      } catch (e) {
        this.setData({ userAvatar: '', isLoggedIn })
      }
    } else {
      this.setData({ userAvatar: '', isLoggedIn })
    }
  },

  onUnload() {
    // 持久化聊天记录（限制数量）
    this._trimAndSave(this.data.messages)
  },

  onInput(e) {
    const value = e.detail.value
    this.setData({ 
      inputValue: value,
      canSend: value.trim().length > 0,
    })
  },

  async send() {
    const app = getApp()
    if (!store.checkLogin()) {
      return wx.showToast({ title: '请先登录', icon: 'none' })
    }
    
    const text = this.data.inputValue.trim()
    if (!text) return

    // 添加用户消息
    const msgs = [...this.data.messages, {role:'user',content:text}]
    this.setData({ messages: msgs, inputValue: '', loading: true, canSend: false })

    try {
      // 调用后端真实API — 即使后端没有LLM也会返回规则匹配的结构化回复
      const history = msgs.map(m => ({ role: m.role, content: m.content }))
      const res = await aiApi.chat(text, history.slice(0, -1))
      
      // aiApi.chat 通过 request.js 自动解包，res 就是 ChatResponse 的 data 字段
      const reply = res.reply || res.content || '抱歉，我没有理解您的意思，请换个问题试试。'
      const replyType = res.type || 'text'

      const newMsgs = [...msgs, {role: 'ai', content: reply, type: replyType}]
      this.setData({ messages: newMsgs, loading: false })
      
      // 限制消息数量，超出时清理最早的消息
      this._trimAndSave(newMsgs)
    } catch (err) {
      console.error('[AI Chat] 请求失败:', err)
      
      // 降级方案：使用本地规则回复（网络不通时的备用）
      const fallbackReply = this._getFallbackReply(text)
      const newMsgs = [...msgs, {role: 'ai', content: fallbackReply}]
      this.setData({ messages: newMsgs, loading: false })
      
      // 限制消息数量，超出时清理最早的消息
      this._trimAndSave(newMsgs)
    }
  },

  /**
   * 限制消息数量并持久化
   * 超过 MAX_MESSAGES 条时自动清理最早的消息
   */
  _trimAndSave(msgs) {
    const trimmed = msgs.length > MAX_MESSAGES ? msgs.slice(-MAX_MESSAGES) : msgs
    this.setData({ messages: trimmed })
    try {
      wx.setStorageSync(CHAT_STORAGE_KEY, trimmed)
    } catch (e) {
      // ignore storage error
    }
  },

  /**
   * 网络不通时的本地降级回复
   */
  _getFallbackReply(text) {
    const t = text.toLowerCase()
    if (t.includes('名片') || t.includes('简介') || t.includes('介绍') || t.includes('文案')) {
      return '我可以帮您生成专业的名片文案！请提供您的姓名、职位和公司信息。'
    }
    if (t.includes('标签') || t.includes('关键词')) {
      return '根据您的信息，推荐以下标签方向：\n\n🏷️ 产品经理\n🏷️ 用户增长\n🏷️ 数据分析\n🏷️ 战略规划\n\n需要调整或添加其他标签吗？'
    }
    if (t.includes('匹配') || t.includes('合作') || t.includes('伙伴')) {
      return '我来帮您分析合作匹配度！请告诉我您需要什么样的合作伙伴。'
    }
    return '🤖 您好！我是您的AI数智名片助手。我可以帮您：\n\n1. ✍️ 生成专业的自我介绍\n2. 🏷️ 智能推荐标签\n3. 📊 分析访客数据\n4. 🎯 匹配潜在合作伙伴\n\n有什么可以帮您的？'
  },

  goLogin() {
    wx.navigateTo({ url: '/pages/login/index' })
  },

  clearChat() {
    wx.showModal({
      title: '清空聊天记录',
      content: '确定要清空所有聊天记录吗？',
      success: (res) => {
        if (res.confirm) {
          const defaultMsg = [{role:'ai',content:'你好！我是AI助手，有什么可以帮助你的？'}]
          this.setData({ messages: defaultMsg })
          try {
            wx.setStorageSync(CHAT_STORAGE_KEY, defaultMsg)
          } catch (e) {}
          wx.showToast({ title: '已清空', icon: 'success' })
        }
      }
    })
  },
})
