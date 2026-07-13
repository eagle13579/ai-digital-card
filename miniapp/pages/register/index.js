/**
 * 完善个人资料页 - 登录后首次使用引导
 * AI数智名片
 *
 * 流程：
 * 1. 登录成功后检测 is_new → 跳转到此页
 * 2. 用户填写表单（姓名、公司、职位、手机号必填）
 * 3. 选填：简介、提供/需求标签、头像
 * 4. 调用 PUT /api/users/me 保存
 * 5. 调用 store.setOnboardingDone() 标记引导完成
 * 6. 跳转到首页
 */
const i18n = require('../../utils/i18n')
const store = require('../../utils/store')
const { userApi } = require('../../utils/api')

Page({
  data: {
    // 表单字段
    name: '',
    company: '',
    title: '',
    phone: '',
    intro: '',
    provide: '',
    need: '',
    avatar: '',

    // 表单验证错误
    errors: {},

    // UI 状态
    loading: false,
    avatarLoading: false,

    // i18n
    _t: {},
  },

  onLoad() {
    this._loadI18n()

    // 从 store 预填已有信息
    const { userInfo } = store.getState()
    if (userInfo) {
      this.setData({
        name: userInfo.name || '',
        company: userInfo.company || '',
        title: userInfo.title || '',
        phone: userInfo.phone || '',
        avatar: userInfo.avatar || '',
      })
    }
  },

  onShow() {
    this._loadI18n()
  },

  /** 加载国际化翻译 */
  _loadI18n() {
    this.setData({ _t: i18n.getTranslations() })
  },

  // ── 头像上传 ───────────────────────────────────────────────

  /** 选择头像 */
  chooseAvatar() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      sizeType: ['compressed'],
      success: (res) => {
        if (res.tempFiles && res.tempFiles.length > 0) {
          const tempFilePath = res.tempFiles[0].tempFilePath
          this.setData({ avatarLoading: true })
          this._uploadAvatar(tempFilePath)
        }
      },
      fail: () => {
        // 用户取消选择，不处理
      },
    })
  },

  /** 上传头像到服务器 */
  _uploadAvatar(filePath) {
    const { token } = store.getState()
    const { API_BASE_URL } = require('../../utils/request')

    wx.uploadFile({
      url: `${API_BASE_URL}/api/upload/avatar`,
      filePath,
      name: 'file',
      header: {
        Authorization: `Bearer ${token}`,
      },
      success: (res) => {
        try {
          const body = JSON.parse(res.data)
          if (res.statusCode >= 200 && res.statusCode < 300) {
            const avatarUrl = body.data?.url || body.url || ''
            this.setData({ avatar: avatarUrl, avatarLoading: false })
            wx.showToast({ title: '头像上传成功', icon: 'success' })
          } else {
            wx.showToast({ title: body.message || '上传失败', icon: 'none' })
            this.setData({ avatarLoading: false })
          }
        } catch (e) {
          wx.showToast({ title: '上传失败', icon: 'none' })
          this.setData({ avatarLoading: false })
        }
      },
      fail: () => {
        wx.showToast({ title: '上传失败', icon: 'none' })
        this.setData({ avatarLoading: false })
      },
    })
  },

  // ── 表单输入 ───────────────────────────────────────────────

  onNameInput(e) {
    this.setData({ name: e.detail.value, 'errors.name': '' })
  },

  onCompanyInput(e) {
    this.setData({ company: e.detail.value, 'errors.company': '' })
  },

  onTitleInput(e) {
    this.setData({ title: e.detail.value, 'errors.title': '' })
  },

  onPhoneInput(e) {
    this.setData({ phone: e.detail.value, 'errors.phone': '' })
  },

  onIntroInput(e) {
    this.setData({ intro: e.detail.value })
  },

  onProvideInput(e) {
    this.setData({ provide: e.detail.value })
  },

  onNeedInput(e) {
    this.setData({ need: e.detail.value })
  },

  // ── 表单验证 ───────────────────────────────────────────────

  /** 验证手机号格式 */
  _isValidPhone(phone) {
    return /^1[3-9]\d{9}$/.test(phone)
  },

  /** 验证表单，返回是否有错误 */
  _validate() {
    const errors = {}
    const { name, company, title, phone } = this.data

    if (!name || !name.trim()) {
      errors.name = this.data._t.registerNameRequired || '请输入姓名'
    }
    if (!company || !company.trim()) {
      errors.company = this.data._t.registerCompanyRequired || '请输入公司'
    }
    if (!title || !title.trim()) {
      errors.title = this.data._t.registerPositionRequired || '请输入职位'
    }
    if (!phone || !phone.trim()) {
      errors.phone = this.data._t.registerPhoneRequired || '请输入手机号'
    } else if (!this._isValidPhone(phone.trim())) {
      errors.phone = this.data._t.registerPhoneInvalid || '手机号格式不正确'
    }

    this.setData({ errors })
    return Object.keys(errors).length === 0
  },

  // ── 提交保存 ───────────────────────────────────────────────

  /** 保存并进入首页 */
  async submitForm() {
    if (!this._validate()) {
      wx.showToast({ title: '请完善必填信息', icon: 'none' })
      return
    }

    this.setData({ loading: true })

    try {
      // 准备提交数据
      const profileData = {
        name: this.data.name.trim(),
        company: this.data.company.trim(),
        title: this.data.title.trim(),
        phone: this.data.phone.trim(),
      }

      // 选填字段
      if (this.data.intro) {
        profileData.intro = this.data.intro.trim()
      }
      if (this.data.avatar) {
        profileData.avatar = this.data.avatar
      }
      if (this.data.provide) {
        profileData.provide = this.data.provide.trim()
      }
      if (this.data.need) {
        profileData.need = this.data.need.trim()
      }

      // 调用 API 更新用户资料
      await userApi.updateProfile(profileData)

      // 更新本地 store
      store.updateUserInfo(profileData)

      // 标记新手引导已完成
      store.setOnboardingDone()

      wx.showToast({
        title: this.data._t.registerSuccess || '资料保存成功',
        icon: 'success',
        duration: 1500,
      })

      setTimeout(() => {
        // 跳转到首页
        wx.switchTab({ url: '/pages/index/index' })
      }, 1500)
    } catch (err) {
      console.error('[Register] 保存资料失败:', err)
      const errMsg = (err && err.message) || '保存失败，请重试'
      wx.showToast({ title: errMsg, icon: 'none' })
      this.setData({ loading: false })
    }
  },

  /** 跳过（不完善资料，直接进入首页） */
  skip() {
    wx.showModal({
      title: '确定跳过吗？',
      content: '跳过之后可以在个人中心随时完善资料',
      success: (res) => {
        if (res.confirm) {
          store.setOnboardingDone()
          wx.switchTab({ url: '/pages/index/index' })
        }
      },
    })
  },
})
