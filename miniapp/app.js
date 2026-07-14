/**
 * AI数智名片 - 微信小程序入口
 * 
 * 全局状态管理已迁移至 utils/store.js（类 Zustand 模式）。
 * app.js 保留生命周期 + 便捷方法，具体状态托管给 store 单例。
 * 
 * 参考: D:\AI询赋拆解\frontend\src\store\index.ts
 */
const store = require('./utils/store')

App({
  onLaunch() {
    // store 构造时已自动从 Storage 恢复 token/userInfo
    const { token } = store.getState()
    console.log('[App] onLaunch, isLoggedIn:', !!token)

    // 检查小程序更新
    this._checkUpdate()
  },

  onShow() {
    // 全局登录守卫：未登录且不在登录页时自动跳转
    const pages = getCurrentPages()
    const currentRoute = pages.length > 0 ? pages[pages.length - 1].route : ''
    const state = this.getState()
    if (!state.isLoggedIn && currentRoute !== 'pages/login/index') {
      wx.navigateTo({ url: '/pages/login/index' })
    }
  },

  onHide() {
    // 小程序切后台
  },

  /**
   * 检查小程序版本更新
   */
  _checkUpdate() {
    const updateManager = wx.getUpdateManager()
    updateManager.onUpdateReady(() => {
      wx.showModal({
        title: '更新提示',
        content: '新版本已准备好，是否重启应用？',
        success: (res) => {
          if (res.confirm) {
            updateManager.applyUpdate()
          }
        },
      })
    })
  },

  // ========== 便捷方法（代理到 store，向下兼容） ==========

  /** 获取全局状态快照 */
  getState() {
    return store.getState()
  },

  /** 检查登录态，未登录跳转登录页 */
  checkLogin() {
    return store.checkLogin()
  },

  /** 设置登录态（token + userInfo） */
  setLogin(token, userInfo) {
    store.setAuth(token, userInfo)
  },

  /** 清除登录态 */
  clearLogin() {
    store.logout()
  },

  /** 更新用户信息 */
  updateUserInfo(userInfo) {
    store.updateUserInfo(userInfo)
  },

  /** 默认分享配置（页面可覆盖） */
  onShareAppMessage() {
    return {
      title: 'AI数智名片 - 智能商务社交',
      path: '/pages/index/index',
    }
  },

  /** 默认分享到朋友圈 */
  onShareTimeline() {
    return { title: 'AI数智名片 - 智能商务社交' }
  },
})
