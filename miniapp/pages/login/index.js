/**
 * 微信授权登录页
 * AI数智名片
 * 
 * 流程（参考 F01_一键登录系统.feature.md）：
 * 1. wx.login() 获取临时 code
 * 2. 向后端 /api/auth/wx-mini-login 发送 code
 * 3. 后端返回 { token, userInfo }
 * 4. 调用 store.setAuth() 持久化登录态
 * 
 * 降级策略：若真实 API 不可用，回退到 MockService（现有逻辑保留）
 */
const store = require('../../utils/store')
const { authApi } = require('../../utils/api')
const { MockService } = require('../../utils/mockService')

Page({
  data: {
    loading: false,
    canIUse: wx.canIUse('button.open-type.getUserInfo'),
    useRealApi: true,
    showError: false,
    errorTitle: '',
    errorDesc: '',
  },

  onLoad() {
    // 登录页始终显示，不自动跳转
    // 登录态由各受保护页面的三层守卫处理
  },

  // 开发测试用：清除登录态回到登录页
  clearLogin() {
    wx.showModal({
      title: '清除登录态',
      content: '确定要退出当前账号，回到登录页吗？',
      success: (res) => {
        if (res.confirm) {
          store.logout()
          wx.clearStorageSync()
          wx.reLaunch({ url: '/pages/login/index' })
        }
      },
    })
  },

  // ========== 微信授权登录（新版 getUserInfo 流程） ==========
  /** 新版 getUserInfo 事件处理 */
  onGetUserInfo(e) {
    this.setData({ loading: true })

    if (e.detail.userInfo) {
      // 用户授权了个人信息，走含用户信息的登录流程
      this._handleUserProfile(e.detail.userInfo)
    } else {
      // 用户拒绝授权，降级为仅 code 登录
      wx.login({
        success: (res) => {
          if (res.code) {
            this._handleLogin(res.code)
          } else {
            wx.showToast({ title: '微信登录失败', icon: 'none' })
            this.setData({ loading: false })
          }
        },
        fail: (err) => {
          console.error('[Login] wx.login 失败:', err)
          wx.showToast({ title: '微信服务异常，请重试', icon: 'none' })
          this.setData({ loading: false })
        },
      })
    }
  },

  /** 降级 / 重试用：直接走 wx.login → code 登录（不获取用户信息） */
  wxLogin() {
    this.setData({ loading: true })
    wx.login({
      success: (res) => {
        if (res.code) {
          this._handleLogin(res.code)
        } else {
          wx.showToast({ title: '微信登录失败', icon: 'none' })
          this.setData({ loading: false })
        }
      },
      fail: (err) => {
        console.error('[Login] wx.login 失败:', err)
        wx.showToast({ title: '微信服务异常，请重试', icon: 'none' })
        this.setData({ loading: false })
      },
    })
  },

  _handleUserProfile(userInfo) {
    wx.login({
      success: (res) => {
        if (res.code) {
          this._handleLoginWithProfile(res.code, userInfo)
        } else {
          wx.showToast({ title: '微信登录失败', icon: 'none' })
          this.setData({ loading: false })
        }
      },
      fail: (err) => {
        console.error('[Login] wx.login 失败:', err)
        wx.showToast({ title: '微信服务异常，请重试', icon: 'none' })
        this.setData({ loading: false })
      },
    })
  },

  _handleLoginWithProfile(code, userInfo) {
    if (this.data.useRealApi) {
      authApi.wxMiniLogin(code, userInfo)
        .then(result => {
          const token = result.access_token
          const mergedUserInfo = { ...(result.user || {}), ...userInfo }

          if (!token) {
            throw new Error('后端未返回 token')
          }

          store.setAuth(token, mergedUserInfo)

          wx.showToast({ title: '登录成功', icon: 'success', duration: 1500 })
          setTimeout(() => {
            wx.switchTab({ url: '/pages/index/index' })
          }, 1500)
        })
        .catch(err => {
          console.error('[Login] API 登录失败:', err)
          if (err && err.message) {
            wx.showToast({ title: err.message, icon: 'none' })
          }
          this.setData({ loading: false })
        })
    } else {
      MockService.login({ code })
        .then(result => {
          if (result.token) {
            const mergedUserInfo = { 
              ...userInfo, 
              ...(result.userInfo || {}),
              name: result.userInfo?.name || userInfo.nickName || userInfo.name,
              avatar: result.userInfo?.avatar || userInfo.avatarUrl || userInfo.avatar,
            }
            store.setAuth(result.token, mergedUserInfo)
            wx.showToast({ title: '登录成功', icon: 'success', duration: 1500 })
            setTimeout(() => {
              wx.switchTab({ url: '/pages/index/index' })
            }, 1500)
          } else {
            wx.showToast({ title: '登录失败', icon: 'none' })
            this.setData({ loading: false })
          }
        })
        .catch(err => {
          console.error('[Login] Mock 登录失败:', err)
          wx.showToast({ title: '网络连接失败，请检查网络', icon: 'none' })
          this.setData({ loading: false })
        })
    }
  },

  /**
   * 处理登录逻辑
   * @param {string} code - wx.login 获取的临时 code
   */
  _handleLogin(code) {
    if (this.data.useRealApi) {
      this._realApiLogin(code)
    } else {
      this._mockLogin(code)
    }
  },

  /**
   * 真实 API 登录（推荐路径）
   * POST /api/auth/wx-mini-login { code }
   * 期望响应格式: { code: 0, data: { token, userInfo } }
   */
  _realApiLogin(code) {
    authApi.wxMiniLogin(code)
      .then(result => {
        // request.js 已解包，result 即后端响应体
        const token = result.access_token
        const userInfo = result.user || {}

        if (!token) {
          throw new Error('后端未返回 token')
        }

        // 更新全局状态
        store.setAuth(token, userInfo)

        wx.showToast({ title: '登录成功', icon: 'success', duration: 1500 })
        setTimeout(() => {
          wx.switchTab({ url: '/pages/index/index' })
        }, 1500)
      })
      .catch(err => {
        console.error('[Login] API 登录失败:', err)
        // 如果使用了 noToast: true，这里需要手动提示
        if (err && err.message) {
          wx.showToast({ title: err.message, icon: 'none' })
        }
        this.setData({ loading: false })
      })
  },

  /**
   * Mock 登录（开发/降级用）
   */
  _mockLogin(code) {
    console.log('[Login] _mockLogin - 开始Mock登录')
    MockService.login({ code })
      .then(result => {
        console.log('[Login] _mockLogin - Mock登录结果:', JSON.stringify(result))
        if (result.token) {
          store.setAuth(result.token, result.userInfo)
          const state = store.getState()
          console.log('[Login] _mockLogin - store状态:', JSON.stringify(state))
          wx.showToast({ title: '登录成功', icon: 'success', duration: 1500 })
          setTimeout(() => {
            wx.switchTab({ url: '/pages/index/index' })
          }, 1500)
        } else {
          wx.showToast({ title: '登录失败', icon: 'none' })
          this.setData({ loading: false })
        }
      })
      .catch(err => {
        console.error('[Login] Mock 登录失败:', err)
        wx.showToast({ title: '网络连接失败，请检查网络', icon: 'none' })
        this.setData({ loading: false })
      })
  },

  // ======== 跳过登录（游客模式） ========
  skipLogin() {
    wx.switchTab({ url: '/pages/index/index' })
  },

  goAgreement() {
    wx.navigateTo({ url: '/pages/agreement/user' })
  },

  goPrivacy() {
    wx.navigateTo({ url: '/pages/agreement/privacy/index' })
  },

  showErrorModal(title, desc) {
    this.setData({
      showError: true,
      errorTitle: title,
      errorDesc: desc,
      loading: false,
    })
  },

  hideError() {
    this.setData({ showError: false })
  },

  retryLogin() {
    this.hideError()
    this.wxLogin()
  },
})
