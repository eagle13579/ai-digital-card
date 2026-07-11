const MockService = require('../../../utils/mockService')

Page({
  data: {
    messages: [{role:'ai',content:'你好！我是AI助手，有什么可以帮助你的？'}],
    inputValue: '',
    loading: false,
    userAvatar: '',
    canSend: false,
    isLoggedIn: false,
  },

  onLoad() {
    const app = getApp()
    const isLoggedIn = app.isLoggedIn()
    
    if (isLoggedIn) {
      const profile = MockService.getUserProfile() || {}
      const userAvatar = (profile && profile.avatar) || (profile && profile.avatarUrl) || ''
      this.setData({ userAvatar, isLoggedIn })
    } else {
      this.setData({ userAvatar: '', isLoggedIn })
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
      this.setData({ messages: [...msgs, {role:'ai',content:'你好！我是AI数智名片助手。我可以帮你生成名片文案、分析匹配度或回答相关问题。请告诉我你的需求。'}], loading: false })
    }, 800)
  },

  goLogin() {
    wx.navigateTo({ url: '/pages/login/index' })
  },
})