/**
 * 轻量全局状态管理
 * AI数智名片 - 微信小程序
 * 
 * 类 Zustand 模式：
 * - 单一 store 单例
 * - 状态变更自动持久化到 Storage
 * - 支持 subscribe 响应式更新
 * - 替代 app.globalData 的全局状态管理
 * 
 * 参考: D:\AI询赋拆解\frontend\src\store\index.ts
 */

const STORAGE_KEYS = {
  TOKEN: 'token',
  USER_INFO: 'userInfo',
}

class Store {
  constructor() {
    this._state = {
      token: this._getStorage('token'),
      userInfo: this._getStorage('userInfo', null),
      isLoggedIn: !!this._getStorage('token'),
      memberLevel: 'free',
      matchCount: 0,
      visitorCount: 0,
      trustCount: 0,
      dataDirty: false,
    }
    this._listeners = []
  }

  /** 安全读取 Storage */
  _getStorage(key, fallback = null) {
    try {
      const val = wx.getStorageSync(key)
      return val !== '' ? val : fallback
    } catch (e) {
      return fallback
    }
  }

  /** 获取当前状态快照 */
  getState() {
    return { ...this._state }
  }

  /** 订阅状态变更 */
  subscribe(listener) {
    this._listeners.push(listener)
    // 返回取消订阅函数
    return () => {
      this._listeners = this._listeners.filter(l => l !== listener)
    }
  }

  /** 通知所有订阅者 */
  _emit() {
    const snapshot = this.getState()
    this._listeners.forEach(fn => {
      try {
        fn(snapshot)
      } catch (e) {
        console.error('[Store] listener error:', e)
      }
    })
  }

  /** 设置登录态：token + userInfo + isLoggedIn */
  setAuth(token, userInfo = null) {
    this._state.token = token
    this._state.userInfo = userInfo
    this._state.isLoggedIn = true
    wx.setStorageSync('token', token)
    if (userInfo) {
      wx.setStorageSync('userInfo', userInfo)
    }
    this._emit()
  }

  /** 登出：清除所有认证态 */
  logout() {
    this._state.token = null
    this._state.userInfo = null
    this._state.isLoggedIn = false
    wx.removeStorageSync('token')
    wx.removeStorageSync('userInfo')
    this._emit()
  }

  /** 检查登录态，未登录则跳转登录页 */
  checkLogin() {
    if (!this._state.isLoggedIn) {
      wx.navigateTo({ url: '/pages/login/index' })
      return false
    }
    return true
  }

  /** 更新用户信息（部分更新） */
  updateUserInfo(partial) {
    if (!partial) return
    this._state.userInfo = { ...(this._state.userInfo || {}), ...partial }
    wx.setStorageSync('userInfo', this._state.userInfo)
    this._emit()
  }

  /** 更新会员等级 */
  updateMemberLevel(level) {
    this._state.memberLevel = level
    this._emit()
  }

  /** 设置统计数据 */
  setStats(stats) {
    if (stats.matchCount !== undefined) this._state.matchCount = stats.matchCount
    if (stats.visitorCount !== undefined) this._state.visitorCount = stats.visitorCount
    if (stats.trustCount !== undefined) this._state.trustCount = stats.trustCount
    this._emit()
  }

  /** 标记数据为脏，首页 onShow 检测后重载 */
  markDataDirty() {
    this._state.dataDirty = true
  }

  /** 清除脏标记 */
  clearDataDirty() {
    this._state.dataDirty = false
  }
}

// 导出单例
const store = new Store()
module.exports = store
