/**
 * 画册创建页面
 * 连接后端 brochureApi + matchApi
 * 提交表单 → 上传图片 → 创建画册 → 触发匹配 → 跳转预览
 */
const { brochureApi, matchApi, membershipApi } = require('../../../utils/api')
const { Logger } = require('../../../utils/util')

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
    },
    newProvide: '',
    newNeed: '',
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
  },

  onLoad() {
    Logger.info('画册创建页', '页面加载')
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
    const value = this.data.newProvide.trim()
    if (!value) {
      wx.showToast({ title: '请输入资源名称', icon: 'none' })
      return
    }
    const provides = [...this.data.formData.provides, value]
    this.setData({
      'formData.provides': provides,
      newProvide: '',
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
    const value = this.data.newNeed.trim()
    if (!value) {
      wx.showToast({ title: '请输入需求名称', icon: 'none' })
      return
    }
    const needs = [...this.data.formData.needs, value]
    this.setData({
      'formData.needs': needs,
      newNeed: '',
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
    try {
      const res = await brochureApi.uploadMedia(filePath, { type: 'image' })
      return res.url || res.data?.url || filePath
    } catch (err) {
      Logger.error('画册创建页', '图片上传失败', err)
      return ''
    }
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
    const contactContent = [
      phone ? `📞 ${phone}` : '',
      email ? `✉️ ${email}` : '',
      wechat ? `💬 ${wechat}` : '',
    ].filter(Boolean).join('\n')

    const providesText = provides.length > 0
      ? '我能提供：\n' + provides.map(p => `• ${p}`).join('\n')
      : ''
    const needsText = needs.length > 0
      ? '我需要的：\n' + needs.map(n => `• ${n}`).join('\n')
      : ''
    const resourcesText = [providesText, needsText].filter(Boolean).join('\n\n')

    const bioText = `姓名：${name}\n职位：${title}\n公司：${displayCompany}\n\n${bio || ''}`

    const pages = []

    // 第0页：封面
    pages.push({
      sort_order: 0,
      content_type: 'cover',
      content: `${name}\n${title}\n${displayCompany}`,
      image_url: avatarUrl || '',
    })

    // 第1页：个人简介
    pages.push({
      sort_order: 1,
      content_type: 'text',
      content: bioText,
      image_url: '',
    })

    // 第2页：资源供需
    if (resourcesText) {
      pages.push({
        sort_order: 2,
        content_type: 'text',
        content: resourcesText,
        image_url: '',
      })
    }

    // 第3页：公司介绍
    const companyText = [
      companyDesc ? `公司简介：\n${companyDesc}` : '',
      development ? `发展历程：\n${development}` : '',
    ].filter(Boolean).join('\n\n')

    if (companyText) {
      pages.push({
        sort_order: pages.length,
        content_type: 'text',
        content: companyText,
        image_url: companyImageUrls[0] || '',
      })
    }

    // 案例页
    for (let i = 0; i < cases.length; i++) {
      const c = cases[i]
      if (!c.name && !c.desc) continue
      const caseContent = [
        c.name ? `案例名称：${c.name}` : '',
        c.date ? `时间：${c.date}` : '',
        c.desc ? `\n${c.desc}` : '',
      ].filter(Boolean).join('\n')
      pages.push({
        sort_order: pages.length,
        content_type: 'text',
        content: caseContent,
        image_url: (caseImageUrlsMap[i] && caseImageUrlsMap[i][0]) || '',
      })
    }

    // 最后一页：联系方式
    pages.push({
      sort_order: pages.length,
      content_type: 'image',
      content: contactContent || `📞 ${phone || '未填写'}`,
      image_url: '',
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
      // ===== 检查会员创建限制 =====
      const membershipRes = await membershipApi.getStatus().catch(() => null)
      const membership = membershipRes?.data ?? membershipRes ?? {}
      const memberLevel = membership.tier || membership.level || 'free'
      const cardCount = membership.card_count ?? membership.cardCount ?? 0
      const cardLimit = membership.card_limit ?? membership.cardLimit ?? (memberLevel === 'free' ? 1 : 10)

      if (memberLevel === 'free' && cardCount >= cardLimit) {
        wx.hideLoading()
        this.setData({ submitting: false })
        wx.showModal({
          title: '升级Pro',
          content: `免费版仅支持${cardLimit}张名片，您已达到上限。升级Pro可创建最多10张名片！`,
          confirmText: '升级Pro',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({ url: '/pages/membership/membership' })
            }
          },
        })
        return
      }

      // ===== 检查批量导入限制（Enterprise功能） =====
      // 批量导入超过10条资源/需求时提示升级Enterprise
      const providesCount = this.data.formData.provides ? this.data.formData.provides.length : 0
      const needsCount = this.data.formData.needs ? this.data.formData.needs.length : 0
      const totalImportItems = providesCount + needsCount
      if (totalImportItems > 10 && memberLevel !== 'enterprise') {
        wx.hideLoading()
        this.setData({ submitting: false })
        wx.showModal({
          title: '升级Enterprise',
          content: `批量导入超过10人需要Enterprise版，当前${memberLevel === 'free' ? 'Free' : 'Pro'}版不支持。升级Enterprise以继续。`,
          confirmText: '升级Enterprise',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({ url: '/pages/membership/membership' })
            }
          },
        })
        return
      }

      const { name, title, company, purpose, provides, needs } = this.data.formData

      // Step 1: 上传头像（如果有）
      let avatarUrl = ''
      if (this.data.formData.avatar) {
        avatarUrl = await this.uploadImage(this.data.formData.avatar)
      }

      // Step 2: 上传公司图片
      const companyImageUrls = await this.uploadImages(this.data.formData.companyImages)

      // Step 3: 上传案例图片
      const caseImagesMap = {}
      for (let i = 0; i < this.data.formData.cases.length; i++) {
        const c = this.data.formData.cases[i]
        if (c.images && c.images.length > 0) {
          caseImagesMap[i] = await this.uploadImages(c.images)
        }
      }

      // Step 4: 构建 pages 并创建画册
      const pages = this.buildPages(avatarUrl, companyImageUrls, caseImagesMap)

      const titleStr = `${name}的${company}名片`

      const brochureData = {
        title: titleStr,
        cover: avatarUrl || '',
        purpose: purpose,
        pages: pages,
      }

      Logger.info('画册创建页', '调用 brochureApi.create', {
        title: titleStr,
        purpose: purpose,
        pagesCount: pages.length,
      })

      const result = await brochureApi.create(brochureData)
      Logger.info('画册创建页', '画册创建成功', { id: result.id })

      // Step 5: 发布画册（生成分享 token）
      let brochureId = result.id
      try {
        const published = await brochureApi.publish(brochureId)
        Logger.info('画册创建页', '画册发布成功', { shareToken: published.share_token })
      } catch (pubErr) {
        Logger.warn('画册创建页', '发布失败，使用未发布状态', pubErr)
      }

      wx.hideLoading()

      // Step 6: 触发匹配引擎（异步，不阻塞跳转）
      this.triggerMatchingAsync(brochureId)

      // Step 7: 跳转到预览页
      wx.showToast({ title: '生成成功', icon: 'success', duration: 1500 })
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
