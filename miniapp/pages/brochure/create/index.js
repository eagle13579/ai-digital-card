/**
 * 画册创建页面
 */
const { MockService } = require('../../../utils/mockService')
const { Logger } = require('../../../utils/util')
const { matchApi } = require('../../../utils/api')

Page({
  data: {
    formData: {
      avatar: '',
      name: '',
      title: '',
      company: '',
      phone: '',
      email: '',
      wechat: '',
      bio: '',
      provides: [],
      needs: [],
      purpose: 'partner',
      companyName: '',
      industry: '',
      companySize: '',
      companyDesc: '',
      development: '',
      companyImages: [],
      cases: [],
      style: 'professional',
      newProvide: '',
      newNeed: '',
    },
    purposeOptions: [
      { value: 'partner', label: '寻找合作伙伴', icon: '🤝' },
      { value: 'client', label: '寻找客户', icon: '🎯' },
      { value: 'investor', label: '寻找投资', icon: '💰' },
      { value: 'supplier', label: '寻找供应商', icon: '🔧' },
    ],
    styleOptions: [
      { value: 'professional', name: '商务专业', desc: '适合商务场合', preview: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)' },
      { value: 'creative', name: '创意活力', desc: '适合设计行业', preview: 'linear-gradient(135deg, #EC4899 0%, #F97316 100%)' },
      { value: 'minimal', name: '极简简约', desc: '适合科技行业', preview: 'linear-gradient(135deg, #64748B 0%, #1E293B 100%)' },
    ],
    sizeOptions: ['1-10人', '11-50人', '51-100人', '101-500人', '501-1000人', '1000人以上'],
    submitting: false,
    /** ChatEditor 对话式编辑 */
      showChatEditor: true,
      cardId: '',
      /** 键盘弹出状态 */
        keyboardActive: false,
        keyboardHeight: 0,
        scrollTop: 0,
    },

    /**
     * 输入框聚焦 — 记录键盘状态
     */
    onInputFocus() {
      this.setData({ keyboardActive: true })
    },

    /**
     * 输入框失焦
     */
    onInputBlur() {
      this.setData({ keyboardActive: false })
    },

    /**
     * 多行文本聚焦 — 滚动scroll-view使所在区域可见
     */
    onTextareaFocus(e) {
      const section = e.currentTarget.dataset.section
      this.setData({ keyboardActive: true })
      // 延迟至键盘弹出后再滚动
      setTimeout(() => {
        wx.createSelectorQuery()
          .select(`#${section}`)
          .boundingClientRect(rect => {
            if (rect && rect.top) {
              this.setData({ scrollTop: Math.max(0, rect.top - 80) })
            }
          })
          .exec()
      }, 400)
    },

    onLoad(options) {
    Logger.info('画册创建页', '页面加载', { options })

    // 获取名片ID（编辑模式）
    if (options && options.id) {
      this.setData({ cardId: options.id })
    }

    // 监听键盘高度变化
    wx.onKeyboardHeightChange(res => {
      this.setData({ keyboardHeight: res.height, keyboardActive: res.height > 0 })
    })
  },

  /**
   * ChatEditor 编辑确认 — 刷新表单数据
   */
  onEditConfirm(e) {
    Logger.info('画册创建页', 'ChatEditor 编辑确认', e.detail)
    // 可以在此从后端刷新表单数据
    // 简单实现：刷新页面数据
    wx.showToast({ title: '修改已应用', icon: 'success' })
  },

  /**
   * ChatEditor 撤销编辑 — 刷新表单数据
   */
  onEditUndo(e) {
    Logger.info('画册创建页', 'ChatEditor 撤销编辑', e.detail)
    // 撤销后刷新表单数据
    wx.showToast({ title: '已撤销', icon: 'success' })
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    this.setData({
      [`formData.${field}`]: value,
    })
  },

  onCaseInput(e) {
    const caseIndex = parseInt(e.currentTarget.dataset.caseIndex)
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    const cases = [...this.data.formData.cases]
    if (!cases[caseIndex]) {
      cases[caseIndex] = {}
    }
    cases[caseIndex][field] = value
    this.setData({
      'formData.cases': cases,
    })
  },

  chooseAvatar() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        this.setData({
          'formData.avatar': res.tempFilePaths[0],
        })
      },
    })
  },

  addProvide() {
    const value = this.data.formData.newProvide ? this.data.formData.newProvide.trim() : ''
    if (!value) {
      wx.showToast({ title: '请输入资源名称', icon: 'none' })
      return
    }
    const provides = [...this.data.formData.provides, value]
    this.setData({
      'formData.provides': provides,
      'formData.newProvide': '',
    })
  },

  removeProvide(e) {
    const index = parseInt(e.currentTarget.dataset.index)
    const provides = this.data.formData.provides.filter((_, i) => i !== index)
    this.setData({
      'formData.provides': provides,
    })
  },

  addNeed() {
    const value = this.data.formData.newNeed ? this.data.formData.newNeed.trim() : ''
    if (!value) {
      wx.showToast({ title: '请输入需求名称', icon: 'none' })
      return
    }
    const needs = [...this.data.formData.needs, value]
    this.setData({
      'formData.needs': needs,
      'formData.newNeed': '',
    })
  },

  removeNeed(e) {
    const index = parseInt(e.currentTarget.dataset.index)
    const needs = this.data.formData.needs.filter((_, i) => i !== index)
    this.setData({
      'formData.needs': needs,
    })
  },

  selectPurpose(e) {
    const value = e.currentTarget.dataset.value
    this.setData({
      'formData.purpose': value,
    })
  },

  showSizePicker() {
    wx.showActionSheet({
      itemList: this.data.sizeOptions,
      success: (res) => {
        this.setData({
          'formData.companySize': this.data.sizeOptions[res.tapIndex],
        })
      },
    })
  },

  chooseCompanyImage() {
    const currentCount = this.data.formData.companyImages && this.data.formData.companyImages.length
      ? this.data.formData.companyImages.length : 0
    wx.chooseImage({
      count: 3 - currentCount,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const images = [...(this.data.formData.companyImages || []), ...res.tempFilePaths]
        this.setData({
          'formData.companyImages': images,
        })
      },
    })
  },

  removeCompanyImage(e) {
    const index = parseInt(e.currentTarget.dataset.index)
    const images = this.data.formData.companyImages.filter((_, i) => i !== index)
    this.setData({
      'formData.companyImages': images,
    })
  },

  addCase() {
    const cases = [...this.data.formData.cases, { name: '', date: '', desc: '', images: [] }]
    this.setData({
      'formData.cases': cases,
    })
  },

  deleteCase(e) {
    const index = parseInt(e.currentTarget.dataset.index)
    const cases = this.data.formData.cases.filter((_, i) => i !== index)
    this.setData({
      'formData.cases': cases,
    })
  },

  chooseCaseImage(e) {
    const caseIndex = parseInt(e.currentTarget.dataset.caseIndex)
    const caseData = this.data.formData.cases[caseIndex] || { images: [] }
    const imageCount = caseData.images && caseData.images.length ? caseData.images.length : 0
    const remaining = 3 - imageCount

    wx.chooseImage({
      count: remaining,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const cases = [...this.data.formData.cases]
        cases[caseIndex] = cases[caseIndex] || { name: '', date: '', desc: '', images: [] }
        cases[caseIndex].images = [...(cases[caseIndex].images || []), ...res.tempFilePaths]
        this.setData({
          'formData.cases': cases,
        })
      },
    })
  },

  removeCaseImage(e) {
    const caseIndex = parseInt(e.currentTarget.dataset.caseIndex)
    const imageIndex = parseInt(e.currentTarget.dataset.imageIndex)
    const cases = [...this.data.formData.cases]
    if (cases[caseIndex] && cases[caseIndex].images) {
      cases[caseIndex].images = cases[caseIndex].images.filter((_, i) => i !== imageIndex)
    }
    this.setData({
      'formData.cases': cases,
    })
  },

  selectStyle(e) {
    const value = e.currentTarget.dataset.value
    this.setData({
      'formData.style': value,
    })
  },

  previewImage(e) {
    const url = e.currentTarget.dataset.url
    wx.previewImage({
      urls: [url],
      current: url,
    })
  },

  validateForm() {
    const { name, title, company, bio, phone, email } = this.data.formData

    if (!name || !name.trim()) {
      wx.showToast({ title: '请输入姓名', icon: 'none' })
      return false
    }
    if (!title || !title.trim()) {
      wx.showToast({ title: '请输入职位', icon: 'none' })
      return false
    }
    if (!company || !company.trim()) {
      wx.showToast({ title: '请输入公司名称', icon: 'none' })
      return false
    }
    return true
  },

  /**
   * 上传单张图片，返回上传后的 URL
   * @param {string} filePath 本地临时文件路径
   * @returns {Promise<string>} 上传后的图片 URL
   */
  async uploadImage(filePath) {
    if (!filePath) return ''
    return filePath
  },

  /**
   * 批量上传图片
   */
  async uploadImages(filePaths) {
    if (!filePaths || filePaths.length === 0) return []
    const urls = []
    for (const fp of filePaths) {
      const url = await this.uploadImage(fp)
      if (url) urls.push(url)
    }
    return urls
  },

  /**
   * 将表单数据转换为后端 pages 数组
   */
  buildPages(avatarUrl, companyImageUrls, caseImageUrlsMap) {
    const { name, title, company, phone, email, wechat, bio, provides, needs,
      purpose, companyName, companyDesc, development, cases } = this.data.formData

    const displayCompany = companyName || company
    const pages = []

    // 第0页：封面
    pages.push({
      type: 'cover',
      title: `${name || '用户'}的AI数智名片`,
      subtitle: `${displayCompany || ''}${displayCompany && title ? ' · ' : ''}${title || ''}`,
      avatar: avatarUrl || '',
    })

    // 第1页：个人简介
    pages.push({
      type: 'profile',
      name: name || '',
      title: title || '',
      company: displayCompany || '',
      bio: bio || '',
      contact: {
        phone: phone || '',
        email: email || '',
        wechat: wechat || '',
      },
    })

    // 第2页：资源供需
    const providesList = provides.length > 0 ? provides.map(p => p) : []
    const needsList = needs.length > 0 ? needs.map(n => n) : []
    if (providesList.length || needsList.length) {
      pages.push({
        type: 'resources',
        provides: providesList,
        needs: needsList,
        purpose: purpose || 'partner',
      })
    }

    // 公司介绍
    if (companyDesc || development) {
      pages.push({
        type: 'company',
        name: displayCompany || '',
        industry: this.data.formData.industry || '',
        size: this.data.formData.companySize || '',
        desc: companyDesc || '',
        development: development || '',
        images: companyImageUrls || [],
      })
    }

    // 案例页
    for (let i = 0; i < cases.length; i++) {
      const c = cases[i]
      if (!c.name && !c.desc) continue
      pages.push({
        type: 'case',
        index: i + 1,
        name: c.name || '',
        date: c.date || '',
        desc: c.desc || '',
        images: (caseImageUrlsMap[i]) || [],
      })
    }

    // 联系方式
    pages.push({
      type: 'contact',
      name: name || '',
      phone: phone || '',
      email: email || '',
      wechat: wechat || '',
      company: displayCompany || '',
    })

    return pages
  },

  async submitForm() {
    if (this.validateForm() === false) return
    if (this.data.submitting) return

    // 检查登录态
    const app = getApp()
    if (!app.globalData.token) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      setTimeout(() => wx.navigateTo({ url: '/pages/login/index' }), 800)
      return
    }

    this.setData({ submitting: true })
    wx.showLoading({ title: '生成中...', mask: true })

    try {
      const { name, title, company, purpose, provides, needs } = this.data.formData

      let avatarUrl = ''
      if (this.data.formData.avatar) {
        avatarUrl = await this.uploadImage(this.data.formData.avatar)
      }

      const companyImageUrls = await this.uploadImages(this.data.formData.companyImages)

      const caseImagesMap = {}
      for (let i = 0; i < this.data.formData.cases.length; i++) {
        const c = this.data.formData.cases[i]
        if (c.images && c.images.length > 0) {
          caseImagesMap[i] = await this.uploadImages(c.images)
        }
      }

      const pages = this.buildPages(avatarUrl, companyImageUrls, caseImagesMap)

      const titleStr = `${name}的${company}名片`

      const brochureData = {
        title: titleStr,
        cover: avatarUrl || '',
        purpose: purpose,
        pages: pages,
        ...this.data.formData,
      }

      Logger.info('画册创建页', '调用 MockService.createBrochure', {
        title: titleStr,
        purpose: purpose,
        pagesCount: pages.length,
      })

      const result = await MockService.createBrochure(brochureData)
      Logger.info('画册创建页', '画册创建成功', { id: result.id })

      wx.hideLoading()

      let brochureId = result.id

      // Step 7: 跳转到预览页
      wx.showToast({ title: '生成成功', icon: 'success', duration: 1500 })

      // 标记首页数据需要刷新
      const app = getApp()
      app.globalData._dataDirty = true

      setTimeout(() => {
        wx.redirectTo({
          url: `/pages/brochure/preview/index?id=${brochureId}`,
        })
      }, 1500)

    } catch (err) {
      wx.hideLoading()
      this.setData({ submitting: false })
      Logger.error('画册创建页', '提交失败', err)
      const errMsg = (err && (err.detail || err.errMsg || err.message)) || '提交失败，请重试'
      wx.showToast({ title: errMsg, icon: 'none', duration: 3000 })
    }
  },

  /**
   * 异步触发匹配引擎（不影响跳转流程）
   */
  async triggerMatchingAsync(brochureId) {
    try {
      await matchApi.triggerMatching(0.3)
      Logger.info('画册创建页', '匹配引擎触发成功', { brochureId })
    } catch (err) {
      Logger.warn('画册创建页', '匹配引擎触发失败（不影响画册创建）', err)
    }
  },
})
