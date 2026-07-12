const { organizationApi } = require('../../../utils/api')
const { MockService } = require('../../../utils/mockService')

Page({
  data: {
    isEdit: false,
    orgId: '',
    saving: false,
    formData: {
      name: '',
      slug: '',
      description: '',
      industry: '',
      size: '1-10',
    },
  },

  onLoad(options) {
    const orgId = options.id
    if (orgId) {
      wx.setNavigationBarTitle({ title: '编辑组织' })
      this.setData({ isEdit: true, orgId: parseInt(orgId, 10) })
      this.loadOrganization()
    }
  },

  async loadOrganization() {
    this.setData({ loading: true })
    try {
      let org = null
      if (!MockService.USE_MOCK) {
        try {
          org = await organizationApi.get(this.data.orgId)
        } catch (e) {
          console.warn('[OrgCreate] 获取组织信息失败:', e)
          org = await this.getMockOrganization()
        }
      } else {
        org = await this.getMockOrganization()
      }
      this.setData({
        formData: {
          name: org.name || '',
          slug: org.slug || '',
          description: org.description || '',
          industry: org.industry || '',
          size: org.size || '1-10',
        },
        loading: false,
      })
    } catch (err) {
      console.error('[OrgCreate] 加载失败:', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  async getMockOrganization() {
    await MockService.mockDelay(200)
    return {
      id: this.data.orgId,
      name: 'AI数智名片技术委员会',
      slug: 'ai-digital-card-tech',
      description: '负责AI数智名片产品的技术研发与标准制定',
      industry: '互联网/软件',
      size: '11-50人',
    }
  },

  onInput(e) {
    const { field } = e.currentTarget.dataset
    this.setData({
      [`formData.${field}`]: e.detail.value,
    })
  },

  onSizeChange(e) {
    const sizes = ['1-10', '11-50', '51-200', '201-500', '500+']
    this.setData({
      'formData.size': sizes[e.detail.value],
    })
  },

  async handleSave() {
    const { formData, isEdit, orgId } = this.data
    if (!formData.name.trim()) {
      wx.showToast({ title: '请填写组织名称', icon: 'none' })
      return
    }
    if (!formData.slug.trim()) {
      formData.slug = formData.name.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]/g, '-').replace(/--+/g, '-').replace(/^-|-$/g, '')
    }
    this.setData({ saving: true })
    try {
      if (isEdit) {
        await organizationApi.update(orgId, formData)
        wx.showToast({ title: '更新成功', icon: 'success' })
      } else {
        await organizationApi.create(formData)
        wx.showToast({ title: '创建成功', icon: 'success' })
      }
      wx.navigateBack()
    } catch (err) {
      console.error('[OrgCreate] 保存失败:', err)
      wx.showToast({ title: err.message || '保存失败', icon: 'none' })
    } finally {
      this.setData({ saving: false })
    }
  },

  goBack() {
    wx.navigateBack()
  },
})
