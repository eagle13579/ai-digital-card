/**
 * 画册创建页面
 * 用户可以上传身份信息、资源供需、公司介绍、产品案例等信息
 * 自动生成可翻页的AI数智名片画册
 */
const { MockService } = require('../../../utils/mockService')
const { Logger } = require('../../../utils/util')
const store = require('../../../utils/store')

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
      school: '',
      major: '',
      education: '',
      skillTags: [],
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
      { value: 'investor', label: '寻找投资', icon: '💰' },
      { value: 'employee', label: '寻找人才', icon: '👥' },
      { value: 'client', label: '寻找客户', icon: '🎯' },
    ],
    styleOptions: [
      { value: 'professional', name: '商务专业', desc: '适合商务场合', preview: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)' },
      { value: 'creative', name: '创意活力', desc: '适合设计行业', preview: 'linear-gradient(135deg, #EC4899 0%, #F97316 100%)' },
      { value: 'minimal', name: '极简简约', desc: '适合科技行业', preview: 'linear-gradient(135deg, #64748B 0%, #1E293B 100%)' },
    ],
    sizeOptions: ['1-10人', '11-50人', '51-100人', '101-500人', '501-1000人', '1000人以上'],
    showMoreInfo: false,
  },

  onLoad() {
    Logger.info('画册创建页', '页面加载')
  },

  toggleMoreInfo() {
    this.setData({
      showMoreInfo: !this.data.showMoreInfo,
    })
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
    const currentCount = this.data.formData.companyImages && this.data.formData.companyImages.length ? this.data.formData.companyImages.length : 0
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
    Logger.info('画册创建页', '开始表单验证', { 
      formData: JSON.stringify(this.data.formData),
      name: this.data.formData.name,
      title: this.data.formData.title,
      company: this.data.formData.company,
      bio: this.data.formData.bio ? this.data.formData.bio.slice(0, 30) + '...' : '',
    })
    
    const { name, title, company, bio } = this.data.formData
    
    Logger.info('画册创建页', '表单字段值', {
      nameValue: name,
      nameLength: name ? name.length : 0,
      nameTrimmed: name ? name.trim() : '',
      titleValue: title,
      companyValue: company,
      bioValue: bio ? bio.slice(0, 50) : '',
      bioLength: bio ? bio.length : 0,
    })
    
    if (!name || !name.trim()) {
      Logger.error('画册创建页', '验证失败', { field: 'name', value: name, reason: '姓名为空' })
      wx.showToast({ title: '请输入姓名', icon: 'none' })
      return false
    }
    if (!title || !title.trim()) {
      Logger.error('画册创建页', '验证失败', { field: 'title', value: title, reason: '职位为空' })
      wx.showToast({ title: '请输入职位', icon: 'none' })
      return false
    }
    if (!company || !company.trim()) {
      Logger.error('画册创建页', '验证失败', { field: 'company', value: company, reason: '公司名称为空' })
      wx.showToast({ title: '请输入公司名称', icon: 'none' })
      return false
    }
    if (bio && bio.length < 50) {
      Logger.warn('画册创建页', '个人简介建议至少50字', { bioLength: bio.length })
    }
    
    Logger.info('画册创建页', '表单验证通过')
    return true
  },

  async submitForm() {
    if (!this.validateForm()) {
      return
    }

    wx.showLoading({ title: '生成中...' })
    try {
      const data = { ...this.data.formData }
      Logger.info('画册创建页', '开始生成画册', { 
        name: data.name,
        company: data.company,
        title: data.title,
        providesCount: data.provides && data.provides.length ? data.provides.length : 0,
        needsCount: data.needs && data.needs.length ? data.needs.length : 0,
        casesCount: data.cases && data.cases.length ? data.cases.length : 0,
      })
      
      const result = await MockService.createBrochure(data)
      Logger.info('画册创建页', '画册生成完成', { result: result ? { id: result.id, title: result.title } : null })
      
      if (result.id) {
        wx.hideLoading()
        wx.showToast({ title: '生成成功', icon: 'success' })
        store.markDataDirty()
        setTimeout(() => {
          wx.navigateTo({
            url: `/pages/brochure/preview/index?id=${result.id}`,
          })
        }, 1500)
      } else {
        wx.hideLoading()
        wx.showToast({ title: '生成失败', icon: 'none' })
      }
    } catch (err) {
      wx.hideLoading()
      Logger.error('画册创建页', '提交失败', err)
      wx.showToast({ title: '提交失败', icon: 'none' })
    }
  },

  onSkillTagsInput(e) {
    const value = e.detail.value
    const tags = value ? value.split(/[,，]/).map(t => t.trim()).filter(t => t) : []
    this.setData({
      'formData.skillTags': tags,
    })
  },
})