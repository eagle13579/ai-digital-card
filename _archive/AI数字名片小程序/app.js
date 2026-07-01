/**
 * AI数字名片 - 微信小程序入口
 * 全局状态管理 + 生命周期
 */
App({
  globalData: {
    userInfo: null,
    token: null,
    memberLevel: 'free',
    matchCount: 0,
    visitorCount: 0,
    trustCount: 0,
  },

  onLaunch() {
    // 从本地缓存恢复登录态
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    if (token) {
      this.globalData.token = token
      this.globalData.userInfo = userInfo
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
  setLogin(token, userInfo) {
    this.globalData.token = token
    this.globalData.userInfo = userInfo
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
