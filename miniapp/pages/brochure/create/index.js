/**
 * 画册创建页面 - 表单Stepper版
 * 4步引导：基本信息 → 专业信息 → 公司信息 → 预览发布
 * 支持行业模板自动匹配
 */
const { brochureApi } = require('../../../utils/api')
const { Logger } = require('../../../utils/util')
const store = require('../../../utils/store')
const i18n = require('../../../utils/i18n')

// ==================== 行业模板配置 ====================
const INDUSTRY_TEMPLATES = {
  tech: {
    label: '科技',
    icon: '💻',
    extraFields: [
      { key: 'techStack', label: '技术栈', placeholder: '如：React, Python, AWS', type: 'text' },
      { key: 'patents', label: '专利/知识产权', placeholder: '请输入专利或知识产权信息', type: 'textarea' },
    ],
  },
  finance: {
    label: '金融',
    icon: '💰',
    extraFields: [
      { key: 'investmentCases', label: '投资案例', placeholder: '请输入投资案例', type: 'textarea' },
      { key: 'certifications', label: '资质认证', placeholder: '请输入资质认证信息', type: 'text' },
    ],
  },
  education: {
    label: '教育',
    icon: '📚',
    extraFields: [
      { key: 'faculty', label: '师资团队', placeholder: '请输入师资团队介绍', type: 'textarea' },
      { key: 'curriculum', label: '课程体系', placeholder: '请输入课程体系介绍', type: 'textarea' },
    ],
  },
  medical: {
    label: '医疗',
    icon: '🏥',
    extraFields: [
      { key: 'academicTitle', label: '学术职务', placeholder: '请输入学术职务', type: 'text' },
      { key: 'thesis', label: '论文/著作', placeholder: '请输入论文或著作', type: 'textarea' },
    ],
  },
  manufacturing: {
    label: '制造',
    icon: '🏭',
    extraFields: [
      { key: 'productionLine', label: '生产线/产能', placeholder: '请输入生产线介绍', type: 'textarea' },
      { key: 'certifications', label: '资质认证', placeholder: '请输入资质认证信息', type: 'text' },
    ],
  },
}

Page({
  data: {
    // ====== 步骤控制 ======
    currentStep: 1,
    totalSteps: 4,

    // ====== 表单数据 ======
    formData: {
      // Step1 基本信息
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
      // Step2 专业信息
      skillTags: [],
      bio: '',
      provides: [],
      needs: [],
      purpose: '',
      purposes: [],
      // Step3 公司信息
      companyName: '',
      industry: '',
      companySize: '',
      companyDesc: '',
      development: '',
      companyImages: [],
      attachmentFile: null,
      industryCustom: '',
      // Step4 预览 - 风格
      style: 'professional',
      // 行业模板扩展字段
      techStack: '',
      patents: '',
      investmentCases: '',
      certifications: '',
      faculty: '',
      curriculum: '',
      academicTitle: '',
      thesis: '',
      productionLine: '',
    },
    newProvide: '',
    newNeed: '',
    skillTagsRaw: '',

    // ====== 行业模板 ======
    industryOptions: [
      { value: 'tech', label: '科技', icon: '💻' },
      { value: 'finance', label: '金融', icon: '💰' },
      { value: 'education', label: '教育', icon: '📚' },
      { value: 'medical', label: '医疗', icon: '🏥' },
      { value: 'manufacturing', label: '制造', icon: '🏭' },
      { value: 'other', label: '其他', icon: '✏️' },
    ],
    currentTemplate: null,
    templateExtraFields: [],

    // ====== 选项数据 ======
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

    // ====== 步骤验证状态 ======
    stepErrors: {
      1: {},
      2: {},
      3: {},
    },

    // ====== 草稿 ======
    draftSaved: false,
    useRealApi: true,
  },

  _draftTimer: null,
  _storageKey: 'brochure_create_draft',

  onLoad() {
    Logger.info('画册创建页', '页面加载')
    // 登录守卫
    if (!store.getState().isLoggedIn) {
      wx.redirectTo({ url: '/pages/login/index' })
      return
    }
    this._setupAutoSave()
    this._checkDraft()
  },

  onUnload() {
    const hasContent = !this._isFormEmpty(this.data.formData)
    if (hasContent) {
      this._saveDraft()
    }
  },

  // ==================== 草稿自动保存/恢复 ====================

  _setupAutoSave() {
    const origSetData = this.setData.bind(this)
    const self = this
    this.setData = function (data, callback) {
      origSetData(data, () => {
        const keys = Object.keys(data)
        const hasFormDataChange = keys.some(k => k === 'formData' || k.startsWith('formData.'))
        if (hasFormDataChange) {
          self._debounceSaveDraft()
        }
        if (typeof callback === 'function') {
          callback()
        }
      })
    }
  },

  _checkDraft() {
    try {
      const draft = wx.getStorageSync(this._storageKey)
      if (draft && draft.formData) {
        const isEmpty = this._isFormEmpty(draft.formData)
        if (!isEmpty) {
          wx.showModal({
            title: '恢复草稿',
            content: '检测到上次未保存的草稿，是否恢复？',
            success: (res) => {
              if (res.confirm) {
                const formData = draft.formData
                // 同步行业模板
                const templateData = this._getIndustryTemplate(formData.industry)
                this.setData({
                  formData,
                  currentTemplate: templateData,
                  templateExtraFields: templateData ? templateData.extraFields : [],
                  draftSaved: true,
                })
                wx.showToast({ title: '草稿已恢复', icon: 'success', duration: 1500 })
              } else {
                this._clearDraft()
              }
            },
          })
        }
      }
    } catch (e) {
      Logger.error('画册创建页', '读取草稿失败', e)
    }
  },

  _isFormEmpty(formData) {
    const textFields = ['name', 'title', 'company', 'phone', 'email', 'wechat', 'bio', 'companyName', 'companyDesc', 'development']
    for (const field of textFields) {
      if (formData[field] && formData[field].toString().trim()) {
        return false
      }
    }
    if (formData.provides && formData.provides.length > 0) return false
    if (formData.needs && formData.needs.length > 0) return false
    if (formData.skillTags && formData.skillTags.length > 0) return false
    if (formData.companyImages && formData.companyImages.length > 0) return false
    if (formData.avatar && formData.avatar.trim()) return false
    return true
  },

  _saveDraft() {
    try {
      wx.setStorageSync(this._storageKey, {
        formData: this.data.formData,
        savedAt: Date.now(),
      })
      this.setData({ draftSaved: true })
    } catch (e) {
      Logger.warn('画册创建页', '保存草稿失败', e)
    }
  },

  _clearDraft() {
    try {
      wx.removeStorageSync(this._storageKey)
      this.setData({ draftSaved: false })
    } catch (e) {
      Logger.warn('画册创建页', '清除草稿失败', e)
    }
  },

  _debounceSaveDraft() {
    if (this._draftTimer) {
      clearTimeout(this._draftTimer)
    }
    this._draftTimer = setTimeout(() => {
      this._saveDraft()
      this._draftTimer = null
    }, 500)
  },

  // ==================== Stepper 导航 ====================

  goNextStep() {
    const step = this.data.currentStep
    if (!this._validateStep(step)) {
      return
    }
    if (step < this.data.totalSteps) {
      this.setData({
        currentStep: step + 1,
      })
    }
  },

  goPrevStep() {
    const step = this.data.currentStep
    if (step > 1) {
      this.setData({
        currentStep: step - 1,
      })
    }
  },

  goToStep(e) {
    const targetStep = parseInt(e.currentTarget.dataset.step)
    const current = this.data.currentStep
    // 只能跳转到已完成的步骤或下一步
    if (targetStep <= current) {
      this.setData({
        currentStep: targetStep,
      })
    }
  },

  _validateStep(step) {
    const { formData } = this.data
    const errors = {}
    let valid = true

    if (step === 1) {
      if (!formData.name || !formData.name.trim()) {
        errors.name = '请输入姓名'
        valid = false
      }
      if (!formData.title || !formData.title.trim()) {
        errors.title = '请输入职位'
        valid = false
      }
      if (!formData.company || !formData.company.trim()) {
        errors.company = '请输入公司名称'
        valid = false
      }
      if (!formData.phone || !formData.phone.trim()) {
        errors.phone = '请输入手机号码'
        valid = false
      }
      // 邮箱非必填
    } else if (step === 2) {
      // 技能标签、合作意向不是严格必填，但bio建议至少50字
      if (formData.bio && formData.bio.length < 10) {
        errors.bio = '个人简介建议至少10字'
        // 不阻止前进，只是提示
      }
    } else if (step === 3) {
      // 公司信息非严格必填
    }

    this.setData({
      [`stepErrors.${step}`]: errors,
    })

    if (!valid) {
      wx.showToast({ title: Object.values(errors)[0], icon: 'none' })
    }
    return valid
  },

  // ==================== 表单字段输入 ====================

  onInput(e) {
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    this.setData({
      [`formData.${field}`]: value,
    })
    // 清除对应字段的错误
    const step = this.data.currentStep
    if (this.data.stepErrors[step] && this.data.stepErrors[step][field]) {
      this.setData({
        [`stepErrors.${step}.${field}`]: undefined,
      })
    }
  },

  // ==================== 头像 ====================

  chooseAvatar() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempPath = res.tempFilePaths[0]
        wx.saveFile({
          tempFilePath: tempPath,
          success: (saveRes) => {
            this.setData({
              'formData.avatar': saveRes.savedFilePath,
            })
          },
          fail: () => {
            this.setData({
              'formData.avatar': tempPath,
            })
          },
        })
      },
    })
  },

  // ==================== 专业信息 - 资源供需 ====================

  onSkillTagsInput(e) {
    const value = e.detail.value
    this.setData({
      skillTagsRaw: value,
    })
  },

  onSkillTagsBlur() {
    const raw = this.data.skillTagsRaw || ''
    const tags = raw ? raw.split(/[,，]/).map(t => t.trim()).filter(t => t) : []
    this.setData({
      'formData.skillTags': tags,
    })
  },

  addProvide() {
    const value = (this.data.formData.newProvide || '').trim()
    if (!value) {
      wx.showToast({ title: '请输入资源名称', icon: 'none' })
      return
    }
    const provides = [...(this.data.formData.provides || []), value]
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
    const value = (this.data.formData.newNeed || '').trim()
    if (!value) {
      wx.showToast({ title: '请输入需求名称', icon: 'none' })
      return
    }
    const needs = [...(this.data.formData.needs || []), value]
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
    const purposes = [...(this.data.formData.purposes || [])]
    const idx = purposes.indexOf(value)
    if (idx === -1) {
      purposes.push(value)
    } else {
      purposes.splice(idx, 1)
    }
    this.setData({
      'formData.purposes': purposes,
    })
  },

  // ==================== 公司信息 ====================

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
        const tempPaths = res.tempFilePaths
        let savedCount = 0
        const savedImages = []

        tempPaths.forEach((path, idx) => {
          wx.saveFile({
            tempFilePath: path,
            success: (saveRes) => {
              savedImages[idx] = saveRes.savedFilePath
            },
            fail: () => {
              savedImages[idx] = path
            },
            complete: () => {
              savedCount++
              if (savedCount === tempPaths.length) {
                const images = [...(this.data.formData.companyImages || []), ...savedImages]
                this.setData({
                  'formData.companyImages': images,
                })
              }
            },
          })
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

  // ==================== 附件文件上传 ====================

  chooseAttachment() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['pdf', 'ppt', 'pptx', 'doc', 'docx', 'xls', 'xlsx', 'zip'],
      success: (res) => {
        const file = res.tempFiles[0]
        // 文件大小限制 10MB
        if (file.size > 10 * 1024 * 1024) {
          wx.showToast({ title: '文件超过10MB限制', icon: 'none' })
          return
        }
        this.setData({
          'formData.attachmentFile': {
            name: file.name,
            size: file.size,
            sizeLabel: this._formatFileSize(file.size),
            path: file.path,
          },
        })
      },
    })
  },

  removeAttachment() {
    this.setData({
      'formData.attachmentFile': null,
    })
  },

  _formatFileSize(bytes) {
    if (!bytes) return ''
    if (bytes < 1024) return bytes + 'B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
    return (bytes / (1024 * 1024)).toFixed(1) + 'MB'
  },

  // ==================== 行业模板 ====================

  /**
   * 获取行业对应的模板配置
   */
  _getIndustryTemplate(industry) {
    if (!industry || !INDUSTRY_TEMPLATES[industry]) return null
    return INDUSTRY_TEMPLATES[industry]
  },

  /**
   * 选择行业 - 自动匹配模板
   */
  selectIndustry(e) {
    const value = e.currentTarget.dataset.value
    if (value === 'other') {
      this.setData({
        'formData.industry': 'other',
        currentTemplate: null,
        templateExtraFields: [],
      })
      return
    }
    const template = this._getIndustryTemplate(value)
    const templateExtraFields = template ? template.extraFields : []

    // 清除旧行业的扩展字段数据
    const resetFields = {}
    if (this.data.currentTemplate) {
      this.data.currentTemplate.extraFields.forEach(f => {
        resetFields[`formData.${f.key}`] = ''
      })
    }

    this.setData({
      'formData.industry': value,
      currentTemplate: template,
      templateExtraFields,
      ...resetFields,
    })
  },

  // ==================== 预览 - 风格选择 ====================

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

  // ==================== 提交 ====================

  validateForm() {
    const { formData } = this.data

    Logger.info('画册创建页', '开始表单验证', {
      name: formData.name,
      title: formData.title,
      company: formData.company,
    })

    if (!formData.name || !formData.name.trim()) {
      wx.showToast({ title: '请输入姓名', icon: 'none' })
      this.setData({ currentStep: 1 })
      return false
    }
    if (!formData.title || !formData.title.trim()) {
      wx.showToast({ title: '请输入职位', icon: 'none' })
      this.setData({ currentStep: 1 })
      return false
    }
    if (!formData.company || !formData.company.trim()) {
      wx.showToast({ title: '请输入公司名称', icon: 'none' })
      this.setData({ currentStep: 1 })
      return false
    }

    return true
  },

  async submitForm() {
    if (!this.validateForm()) {
      return
    }

    wx.showLoading({ title: '生成中...' })
    try {
      const fd = this.data.formData
      Logger.info('画册创建页', '开始生成画册', {
        name: fd.name,
        company: fd.company,
        industry: fd.industry,
      })

      // 如果有微信本地头像路径(wxfile://)，先上传到服务器获取HTTPS URL
      let coverUrl = fd.avatar || ''
      if (coverUrl && coverUrl.startsWith('wxfile://')) {
        try {
          Logger.info('画册创建页', '上传本地头像', { path: coverUrl.substring(0, 40) + '...' })
          wx.showLoading({ title: '上传头像...' })
          coverUrl = await brochureApi.uploadCover(coverUrl)
          Logger.info('画册创建页', '头像上传成功', { url: coverUrl })
        } catch (uploadErr) {
          Logger.warn('画册创建页', '头像上传失败，使用原路径', uploadErr)
          // 上传失败不阻塞流程，封面显示占位符
        }
      }

      // 上传公司图片
      let companyImageUrls = []
      if (fd.companyImages && fd.companyImages.length > 0) {
        wx.showLoading({ title: '上传图片...' })
        for (const imgPath of fd.companyImages) {
          if (imgPath && imgPath.startsWith('wxfile://')) {
            try {
              const url = await brochureApi.uploadCover(imgPath)
              companyImageUrls.push(url)
            } catch (e) {
              Logger.warn('画册创建页', '公司图片上传失败，使用本地路径', e)
              // 上传失败用原路径降级（仅上传者设备可见）
              companyImageUrls.push(imgPath)
            }
          } else if (imgPath) {
            companyImageUrls.push(imgPath)
          }
        }
      }

      // 构建后端期望的 brochure/pages 结构
      const industry = fd.industry === 'other' ? fd.industryCustom : fd.industry
      const skillTags = fd.skillTags || []
      const purposes = (fd.purposes && fd.purposes.length > 0)
        ? fd.purposes.join(',')
        : (fd.purpose || '')
      const pages = [
        {
          content_type: 'profile',
          content: JSON.stringify({
            name: fd.name || '',
            title: fd.title || '',
            company: fd.company || '',
            email: fd.email || '',
            phone: fd.phone || '',
            wechat: fd.wechat || '',
            bio: fd.bio || '',
            provides: fd.provides || [],
            needs: fd.needs || [],
            purpose: purposes,
            education: fd.education || '',
            school: fd.school || '',
            major: fd.major || '',
            industry: industry || '',
            companySize: fd.companySize || '',
            companyDesc: fd.companyDesc || '',
            development: fd.development || '',
            style: fd.style || 'professional',
          }),
          sort_order: 0,
        },
      ]

      // 如果有公司信息，添加公司介绍页
      const companyName = fd.companyName || fd.company || ''
      const companyDesc = fd.companyDesc || ''
      const development = fd.development || ''

      // 上传附件文件
      let attachmentData = null
      if (fd.attachmentFile && fd.attachmentFile.path) {
        wx.showLoading({ title: '上传文件...' })
        try {
          const uploadResult = await brochureApi.uploadFile(fd.attachmentFile.path)
          attachmentData = {
            name: fd.attachmentFile.name,
            url: uploadResult.url,
            size: fd.attachmentFile.size,
          }
        } catch (e) {
          Logger.warn('画册创建页', '附件上传失败，使用本地路径', e)
          // 上传失败用本地路径降级（仅上传者设备可打开）
          attachmentData = {
            name: fd.attachmentFile.name,
            url: fd.attachmentFile.path,
            size: fd.attachmentFile.size,
          }
        }
      }

      if (companyName || companyDesc || development || companyImageUrls.length > 0 || attachmentData) {
        pages.push({
          content_type: 'company',
          content: JSON.stringify({
            name: companyName,
            desc: companyDesc,
            development: development,
            industry: industry || '',
            size: fd.companySize || '',
            images: companyImageUrls,
            attachments: attachmentData ? [attachmentData] : [],
          }),
          sort_order: 1,
        })
      }

      const pageData = {
        title: (fd.name || '未知') + '的电子名片',
        cover: coverUrl,
        purpose: purposes,
        album_meta: null,
        pages,
      }

      let result
      if (this.data.useRealApi) {
        result = await brochureApi.create(pageData)
      }
      Logger.info('画册创建页', '画册生成完成', { result: result ? { id: result.id, title: result.title } : null })

      if (result && result.id) {
        wx.setStorageSync('last_brochure', result)
      }

      if (result && result.id) {
        wx.hideLoading()
        // 生成成功后保留草稿(不清除)，方便用户再次修改
        wx.showToast({ title: '生成成功', icon: 'success' })
        // 同步用户信息到store，确保头像/姓名在全站更新
        store.updateUserInfo({
          name: fd.name || '',
          avatar: coverUrl || fd.avatar || '',
          company: fd.company || '',
          title: fd.title || '',
        })
        store.markDataDirty()
        setTimeout(() => {
          wx.navigateTo({
            url: `/pages/brochure/preview/index?id=${result.id}&created=1`,
          })
        }, 1500)
      } else {
        wx.hideLoading()
        wx.showToast({ title: '生成失败', icon: 'none' })
      }
    } catch (err) {
      wx.hideLoading()
      console.error('[BrochureCreate] 提交失败详情:', err)
      Logger.error('画册创建页', '提交失败', err)
      const errMsg = err.message || (err.data && err.data.message) || '提交失败'
      wx.showToast({ title: errMsg, icon: 'none' })
    }
  },
})
