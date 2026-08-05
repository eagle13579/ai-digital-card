const { organizationApi } = require('../../../utils/api')
const { MockService } = require('../../../utils/mockService')

Page({
  data: {
    organizations: [],
    loading: true,
    showCreateModal: false,
    creating: false,
    formData: {
      name: '',
      slug: '',
      description: '',
      industry: '',
      size: '1-10',
    },
  },

  onShow() {
    this.loadOrganizations()
  },

  async loadOrganizations() {
    this.setData({ loading: true })
    try {
      let organizations = []
      if (!MockService.USE_MOCK) {
        try {
          organizations = await organizationApi.list()
        } catch (err) {
          console.warn('[OrgList] 真实API失败，降级Mock:', err)
          organizations = await this.getMockOrganizations()
        }
      } else {
        organizations = await this.getMockOrganizations()
      }
      this.setData({ organizations, loading: false })
    } catch (err) {
      console.error('[OrgList] 加载失败:', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  async getMockOrganizations() {
    await MockService.mockDelay(300, 600)
    return [
      {
        id: 1,
        name: 'AI数智名片技术委员会',
        slug: 'ai-digital-card-tech',
        description: '负责AI数智名片产品的技术研发与标准制定',
        industry: '互联网/软件',
        size: '11-50人',
        owner_id: 1,
        member_count: 15,
        invite_count: 2,
        is_active: true,
        created_at: new Date(Date.now() - 86400000 * 45).toISOString(),
      },
      {
        id: 2,
        name: '市场合作联盟',
        slug: 'marketing-alliance',
        description: '联合市场推广与品牌合作',
        industry: '市场营销',
        size: '1-10人',
        owner_id: 2,
        member_count: 8,
        invite_count: 0,
        is_active: true,
        created_at: new Date(Date.now() - 86400000 * 20).toISOString(),
      },
      {
        id: 3,
        name: '产业创新中心',
        slug: 'industry-innovation',
        description: '推动产业数字化转型与创新合作',
        industry: '企业服务',
        size: '51-200人',
        owner_id: 1,
        member_count: 42,
        invite_count: 5,
        is_active: true,
        created_at: new Date(Date.now() - 86400000 * 60).toISOString(),
      },
    ]
  },

  goToCreate() {
    this.setData({
      showCreateModal: true,
      formData: { name: '', slug: '', description: '', industry: '', size: '1-10' },
    })
  },

  closeCreateModal() {
    this.setData({ showCreateModal: false })
  },

  stopPropagation() {},

  onInput(e) {
    const { field } = e.currentTarget.dataset
    this.setData({
      [`formData.${field}`]: e.detail.value,
    })
  },

  async handleCreate() {
    const { formData } = this.data
    if (!formData.name.trim()) {
      wx.showToast({ title: '请填写组织名称', icon: 'none' })
      return
    }
    if (!formData.slug.trim()) {
      formData.slug = formData.name.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]/g, '-').replace(/--+/g, '-').replace(/^-|-$/g, '')
    }
    this.setData({ creating: true })
    try {
      await organizationApi.create(formData)
      wx.showToast({ title: '创建成功', icon: 'success' })
      this.closeCreateModal()
      this.loadOrganizations()
    } catch (err) {
      console.error('[OrgList] 创建失败:', err)
      wx.showToast({ title: err.message || '创建失败', icon: 'none' })
    } finally {
      this.setData({ creating: false })
    }
  },

  onSizeChange(e) {
    const sizes = ['1-10', '11-50', '51-200', '201-500', '500+']
    this.setData({
      'formData.size': sizes[e.detail.value],
    })
  },

  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/organization/detail/index?id=${id}` })
  },

  getInitial(name) {
    return (name || 'O')[0]
  },
})
