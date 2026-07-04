/**
 * 创建资源平台 — 发布资源供需
 * 支持: 资源标题/类型/描述/联系方式/预算
 */
const { MockService } = require('../../../utils/mockService')
const { Logger } = require('../../../utils/util')

Page({
  data: {
    // 表单
    title: '',
    type: 'supply', // supply | demand
    category: '',
    description: '',
    budget: '',
    contact: '',
    agreed: false,

    // 状态
    submitting: false,
    showUpgrade: false,
    showPolicy: false,

    // 配额
    quotaRemaining: 3,
    memberLevel: 'free',

    // 分类选项
    categories: ['资金投资', '技术合作', '资源对接', '人才招聘', '市场渠道', '供应链'],
  },

  onLoad() {
    this.loadQuota()
  },

  loadQuota() {
    const app = getApp()
    const level = app.globalData.memberLevel || 'free'
    const quotaMap = { free: 3, gold: 10, diamond: 50, board: 999 }
    this.setData({
      memberLevel: level,
      quotaRemaining: quotaMap[level] || 3,
    })
  },

  onTitleInput(e) {
    this.setData({ title: e.detail.value })
  },
  onDescInput(e) {
    this.setData({ description: e.detail.value })
  },
  onBudgetInput(e) {
    this.setData({ budget: e.detail.value })
  },
  onContactInput(e) {
    this.setData({ contact: e.detail.value })
  },

  selectType(e) {
    const type = e.currentTarget.dataset.type
    this.setData({ type })
  },

  selectCategory(e) {
    this.setData({ category: e.currentTarget.dataset.cat })
  },

  toggleAgree() {
    this.setData({ agreed: !this.data.agreed })
  },

  canSubmit() {
    const { title, category, description, contact, agreed } = this.data
    return title.trim() && category && description.trim() && contact.trim() && agreed
  },

  async submit(e) {
    if (!this.canSubmit()) {
      wx.showToast({ title: '请完善表单', icon: 'none' })
      return
    }

    if (this.data.quotaRemaining <= 0) {
      this.setData({ showUpgrade: true })
      return
    }

    this.setData({ submitting: true })

    try {
      const formData = {
        title: this.data.title.trim(),
        type: this.data.type,
        category: this.data.category,
        description: this.data.description.trim(),
        budget: this.data.budget.trim(),
        contact: this.data.contact.trim(),
      }

      const result = await MockService.createResource(formData)

      if (result && result.success) {
        wx.showToast({ title: '发布成功！', icon: 'success' })
        // 返回上一页
        setTimeout(() => wx.navigateBack(), 1500)
      } else {
        wx.showToast({ title: result?.message || '发布失败', icon: 'none' })
      }
    } catch (err) {
      Logger.error('资源平台', '发布失败', err)
      wx.showToast({ title: '网络错误，请重试', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  },

  // 升级弹窗
  closeUpgrade() {
    this.setData({ showUpgrade: false })
  },
  goUpgrade() {
    wx.showToast({ title: '升级功能开发中', icon: 'none' })
  },

  // 服务协议
  openPolicy() {
    this.setData({ showPolicy: true })
  },
  closePolicy() {
    this.setData({ showPolicy: false })
  },
})
