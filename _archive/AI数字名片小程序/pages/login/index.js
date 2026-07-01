/**
 * 微信授权登录页
 * 使用 wx.login() 获取临时 code → 后端换取 session
 */
const { miniappApi } = require('../../utils/api')

Page({
  data: {
    loading: false,
    canIUse: wx.canIUse('button.open-type.getUserInfo'),
  },

  onLoad() {
    // 检查是否已登录
    const app = getApp()
    if (app.globalData.token) {
      wx.switchTab({ url: '/pages/index/index' })
    }
  },

  // 微信授权登录
  wxLogin() {
    const app = getApp()
    this.setData({ loading: true })
    
    wx.login({
      success: (res) => {
        if (res.code) {
          // 将 code 发给后端
          miniappApi.login({ code: res.code })
            .then(result => {
              if (result.token) {
                // 获取用户信息
                wx.getUserProfile({
                  desc: '用于展示名片信息',
                  success: (profile) => {
                    app.setLogin(result.token, {
                      name: profile.userInfo.nickName,
                      avatar: profile.userInfo.avatarUrl,
                    })
                    wx.switchTab({ url: '/pages/index/index' })
                  },
                  fail: () => {
                    // 用户拒绝授权也能登录（只是没头像昵称）
                    app.setLogin(result.token, { name: '用户' })
                    wx.switchTab({ url: '/pages/index/index' })
                  }
                })
              } else {
                wx.showToast({ title: '登录失败', icon: 'none' })
                this.setData({ loading: false })
              }
            })
            .catch(err => {
              console.error('登录请求失败:', err)
              wx.showToast({ title: '网络连接失败，请检查网络', icon: 'none' })
              this.setData({ loading: false })
            })
        } else {
          wx.showToast({ title: '微信登录失败', icon: 'none' })
          this.setData({ loading: false })
        }
      },
      fail: (err) => {
        console.error('wx.login失败:', err)
        wx.showToast({ title: '微信服务异常，请重试', icon: 'none' })
        this.setData({ loading: false })
      }
    })
  },

  // 跳过登录（游客模式）
  skipLogin() {
    wx.switchTab({ url: '/pages/index/index' })
  },
})
