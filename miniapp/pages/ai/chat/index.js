const MockService = require('../../../utils/mockService')
const CHAT_STORAGE_KEY = 'ai_chat_messages'

Page({
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
        this.setData({ messages: saved })
      } else {
        this.setData({
          messages: [{role:'ai',content:'你好！我是AI助手，有什么可以帮助你的？'}]
        })
      }
    } catch (e) {
      this.setData({
        messages: [{role:'ai',content:'你好！我是AI助手，有什么可以帮助你的？'}]
      })
    }

    const app = getApp()
    const isLoggedIn = app.isLoggedIn()
    
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
    // 持久化聊天记录
    try {
      wx.setStorageSync(CHAT_STORAGE_KEY, this.data.messages)
    } catch (e) {
      // ignore storage error
    }
  },

  onInput(e) {
    const value = e.detail.value
    this.setData({ 
      inputValue: value,
      canSend: value.trim().length > 0,
    })
  },

  send() {
    const app = getApp()
    if (!app.isLoggedIn()) {
      return wx.showToast({ title: '请先登录', icon: 'none' })
    }
    
    const text = this.data.inputValue.trim()
    if (!text) return
    const msgs = [...this.data.messages, {role:'user',content:text}]
    this.setData({ messages: msgs, inputValue: '', loading: true })
    setTimeout(() => {
      const newMsgs = [...msgs, {role:'ai',content:'你好！我是AI数智名片助手。我可以帮你生成名片文案、分析匹配度或回答相关问题。请告诉我你的需求。'}]
      this.setData({ messages: newMsgs, loading: false })
      // 每次发送后自动持久化
      try {
        wx.setStorageSync(CHAT_STORAGE_KEY, newMsgs)
      } catch (e) {}
    }, 800)
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