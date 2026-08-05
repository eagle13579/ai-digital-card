const { teamApi } = require('../../../utils/api')
const { MockService } = require('../../../utils/mockService')

Page({
  data: {
    teams: [],
    loading: true,
    showCreateModal: false,
    creating: false,
    formData: {
      name: '',
      slug: '',
      description: '',
      industry: '',
      size: '1-10',
      max_members: 50,
    },
  },

  onShow() {
    this.loadTeams()
  },

  async loadTeams() {
    this.setData({ loading: true })
    try {
      // 优先走真实API, 降级到Mock
      let teams = []
      if (!MockService.USE_MOCK) {
        try {
          teams = await teamApi.list()
        } catch (err) {
          console.warn('[TeamList] 真实API失败，降级Mock:', err)
          teams = await this.getMockTeams()
        }
      } else {
        teams = await this.getMockTeams()
      }
      this.setData({ teams, loading: false })
    } catch (err) {
      console.error('[TeamList] 加载失败:', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  async getMockTeams() {
    await MockService.mockDelay(300, 600)
    return [
      {
        id: 1,
        name: 'AI数智名片开发组',
        slug: 'ai-digital-card-dev',
        description: '负责AI数智名片产品的研发与维护',
        industry: '互联网/软件',
        size: '11-50人',
        owner_id: 1,
        max_members: 50,
        member_count: 12,
        invite_count: 3,
        is_active: true,
        created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
      },
      {
        id: 2,
        name: '市场运营团队',
        slug: 'marketing-ops',
        description: '产品市场推广与用户运营',
        industry: '市场营销',
        size: '1-10人',
        owner_id: 2,
        max_members: 20,
        member_count: 8,
        invite_count: 1,
        is_active: true,
        created_at: new Date(Date.now() - 86400000 * 15).toISOString(),
      },
      {
        id: 3,
        name: '战略合作伙伴',
        slug: 'strategic-partners',
        description: '与重要合作伙伴的协作团队',
        industry: '商务合作',
        size: '1-10人',
        owner_id: 1,
        max_members: 30,
        member_count: 5,
        invite_count: 0,
        is_active: true,
        created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
      },
    ]
  },

  goToCreate() {
    this.setData({
      showCreateModal: true,
      formData: { name: '', slug: '', description: '', industry: '', size: '1-10', max_members: 50 },
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
      wx.showToast({ title: '请填写团队名称', icon: 'none' })
      return
    }
    if (!formData.slug.trim()) {
      // 自动生成slug
      formData.slug = formData.name.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]/g, '-').replace(/--+/g, '-').replace(/^-|-$/g, '')
    }
    this.setData({ creating: true })
    try {
      await teamApi.create(formData)
      wx.showToast({ title: '创建成功', icon: 'success' })
      this.closeCreateModal()
      this.loadTeams()
    } catch (err) {
      console.error('[TeamList] 创建失败:', err)
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

  goToManage(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/team/manage/index?id=${id}` })
  },

  getInitial(name) {
    return (name || 'T')[0]
  },
})
