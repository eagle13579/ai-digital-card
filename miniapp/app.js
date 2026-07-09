/**
 * AI数智名片 - 微信小程序入口
 * 全局状态管理 + 生命周期
 *
 * API 基础地址通过 config/config.js 统一管理（开发/生产双模式切换）
 */
const config = require('./config/config')

App({
  globalData: {
    userInfo: null,
    token: null,
    openid: '',
    memberLevel: 'free',
    matchCount: 0,
    visitorCount: 0,
    trustCount: 0,
    // API 基础地址 — 从 config.js 读取，开发/生产自动切换
    apiBaseUrl: config.apiBaseUrl,
    // 开发模式标志 — 开发环境下跳过登录阻断，方便调试
    __DEV_MODE__: config.apiBaseUrl === 'http://127.0.0.1:8002',
  },

  onLaunch() {
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    const openid = wx.getStorageSync('openid')
    if (token) {
      this.globalData.token = token
      this.globalData.userInfo = userInfo
      if (openid) {
        this.globalData.openid = openid
      }
      wx.request({
        url: this.globalData.apiBaseUrl + '/api/v1/users/me',
        header: { 'Authorization': 'Bearer ' + token },
        timeout: 8000,
        fail: () => {},
        complete: (res) => {
          if (res.statusCode === 401) {
            this.clearLogin()
            const pages = getCurrentPages()
            const currentPage = pages[pages.length - 1]
            if (currentPage && currentPage.route !== 'pages/login/index') {
              wx.reLaunch({ url: '/pages/login/index' })
            }
          }
        }
      })
    }
  },

  onShow() {
    // 小程序切前台时刷新数据
  },

  // 检查登录态，未登录跳转授权
  checkLogin() {
    if (!this.globalData.token) {
      wx.navigateTo({ url: '/pages/login/index' })
      return false
    }
    return true
  },

  // 设置登录态
  setLogin(token, userInfo, memberLevel, openid) {
    this.globalData.token = token
    this.globalData.userInfo = userInfo
    if (memberLevel) {
      this.globalData.memberLevel = memberLevel
    }
    if (openid) {
      this.globalData.openid = openid
      wx.setStorageSync('openid', openid)
    }
    wx.setStorageSync('token', token)
    wx.setStorageSync('userInfo', userInfo)
  },

  // 清除登录态
  clearLogin() {
    this.globalData.token = null
    this.globalData.userInfo = null
    wx.removeStorageSync('token')
    wx.removeStorageSync('userInfo')
  },

  // 更新用户信息
  updateUserInfo(userInfo) {
    this.globalData.userInfo = { ...this.globalData.userInfo, ...userInfo }
    wx.setStorageSync('userInfo', this.globalData.userInfo)
  },

  // 更新会员等级
  updateMemberLevel(level) {
    this.globalData.memberLevel = level
  },
})
