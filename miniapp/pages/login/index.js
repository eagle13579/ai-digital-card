/**
 * 微信授权登录页
 * 使用 wx.login() 获取临时 code → 后端 /api/v1/auth/wx-mini-login 换取 JWT token
 * 同时获取微信用户信息（头像、昵称等）
 */
const { MockService } = require('../../utils/mockService')

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

  // 获取微信用户信息（open-type=getUserInfo 回调）
  onGetUserInfo(e) {
    if (e.detail.errMsg && e.detail.errMsg.indexOf('fail') >= 0) {
      wx.showToast({ title: '需要授权才能使用微信登录', icon: 'none' })
      return
    }
    if (!e.detail.userInfo) {
      wx.showToast({ title: '获取用户信息失败', icon: 'none' })
      return
    }
    const userInfo = e.detail.userInfo
    this.setData({ loading: true })
    this._doLogin(userInfo)
  },

  _doLogin(userInfo) {
    const app = getApp()
    wx.login({
      success: (res) => {
        if (res.code) {
          const loginData = { code: res.code }
          if (userInfo) {
            loginData.user_info = {
              nickName: userInfo.nickName,
              avatarUrl: userInfo.avatarUrl,
              gender: userInfo.gender,
              country: userInfo.country,
              province: userInfo.province,
              city: userInfo.city,
            }
          }
          MockService.wxMiniLogin(loginData)
            .then(result => {
              if (result.token && result.userInfo) {
                app.setLogin(result.token, result.userInfo)
                if (result.memberLevel) {
                  app.globalData.memberLevel = result.memberLevel
                }
                wx.switchTab({ url: '/pages/index/index' })
              } else {
                wx.showToast({ title: '登录失败，返回数据异常', icon: 'none' })
                this.setData({ loading: false })
              }
            })
            .catch(err => {
              console.error('微信登录请求失败:', err)
              const errMsg = (err && (err.detail || err.errMsg || err.message)) || '网络连接失败，请检查网络'
              wx.showToast({ title: errMsg, icon: 'none' })
              this.setData({ loading: false })
            })
        } else {
          wx.showToast({ title: '微信登录失败（获取code失败）', icon: 'none' })
          this.setData({ loading: false })
        }
      },
      fail: (err) => {
        console.error('wx.login调用失败:', err)
        wx.showToast({ title: '微信服务异常，请重试', icon: 'none' })
        this.setData({ loading: false })
      },
    })
  },

  // 跳转用户协议
  goAgreement() {
    wx.navigateTo({ url: '/pages/agreement/user' })
  },

  // 跳转隐私政策
  goPrivacy() {
    wx.navigateTo({ url: '/pages/agreement/privacy/privacy' })
  },

  // 跳过登录（游客模式）
  skipLogin() {
    wx.switchTab({ url: '/pages/index/index' })
  },
})
