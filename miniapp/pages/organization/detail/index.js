const { organizationApi } = require('../../../utils/api')
const { MockService } = require('../../../utils/mockService')

Page({
  data: {
    orgId: '',
    organization: null,
    members: [],
    invites: [],
    currentUserRole: 'member',
    currentUserId: '',
    loading: true,
    activeTab: 'members',
    showInviteModal: false,
    inviteForm: { email: '', phone: '', message: '' },
    inviting: false,
  },

  onLoad(options) {
    const orgId = parseInt(options.id, 10)
    if (!orgId) {
      wx.showToast({ title: '参数错误', icon: 'none' })
      wx.navigateBack()
      return
    }
    this.setData({ orgId })
    this.loadData()
  },

  onShow() {
    if (this.data.orgId) {
      this.loadData()
    }
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const [organization, members, invites] = await Promise.all([
        this.fetchOrganization(),
        this.fetchMembers(),
        this.fetchInvites(),
      ])
      const { userInfo } = require('../../../utils/store').getState()
      const currentUserId = userInfo?.id || ''
      const isOwner = organization.owner_id === currentUserId || String(organization.owner_id) === String(currentUserId)
      const currentUserRole = isOwner ? 'owner' : 'member'
      this.setData({
        organization,
        members,
        invites,
        currentUserId,
        currentUserRole,
        loading: false,
      })
    } catch (err) {
      console.error('[OrgDetail] 加载失败:', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  async fetchOrganization() {
    if (!MockService.USE_MOCK) {
      try {
        return await organizationApi.get(this.data.orgId)
      } catch (e) {
        console.warn('[OrgDetail] 获取组织详情失败:', e)
      }
    }
    await MockService.mockDelay(200)
    return {
      id: this.data.orgId,
      name: 'AI数智名片技术委员会',
      slug: 'ai-digital-card-tech',
      description: '负责AI数智名片产品的技术研发与标准制定',
      industry: '互联网/软件',
      size: '11-50人',
      owner_id: 1,
      member_count: 15,
      invite_count: 2,
      is_active: true,
      created_at: new Date().toISOString(),
    }
  },

  async fetchMembers() {
    if (!MockService.USE_MOCK) {
      try {
        return await organizationApi.members(this.data.orgId)
      } catch (e) {
        console.warn('[OrgDetail] 获取成员列表失败:', e)
      }
    }
    await MockService.mockDelay(200)
    return [
      { id: 1, user_id: 'u001', name: '张伟', avatar: '', phone: '', company: '科技创新有限公司', title: '产品经理', role: 'owner', joined_at: new Date().toISOString() },
      { id: 2, user_id: 'u002', name: '李娜', avatar: '', phone: '', company: '金融投资集团', title: '投资总监', role: 'admin', joined_at: new Date().toISOString() },
      { id: 3, user_id: 'u003', name: '王强', avatar: '', phone: '', company: '人工智能研究院', title: '首席技术官', role: 'member', joined_at: new Date().toISOString() },
      { id: 4, user_id: 'u004', name: '赵丽', avatar: '', phone: '', company: '互联网公司', title: '技术总监', role: 'member', joined_at: new Date().toISOString() },
      { id: 5, user_id: 'u005', name: '陈明', avatar: '', phone: '', company: '创业孵化平台', title: '孵化总监', role: 'member', joined_at: new Date().toISOString() },
    ]
  },

  async fetchInvites() {
    if (!MockService.USE_MOCK) {
      try {
        return await organizationApi.invites(this.data.orgId)
      } catch (e) {
        console.warn('[OrgDetail] 获取邀请列表失败:', e)
      }
    }
    await MockService.mockDelay(200)
    return [
      { id: 1, org_id: this.data.orgId, invitee_email: 'test@example.com', invitee_phone: '', role: 'member', status: 'pending', created_at: new Date().toISOString(), inviter_id: 'u001' },
      { id: 2, org_id: this.data.orgId, invitee_email: 'newuser@example.com', invitee_phone: '', role: 'admin', status: 'pending', created_at: new Date().toISOString(), inviter_id: 'u001' },
    ]
  },

  switchTab(e) {
    const { tab } = e.currentTarget.dataset
    this.setData({ activeTab: tab })
  },

  goBack() {
    wx.navigateBack()
  },

  isOwner() {
    return this.data.currentUserRole === 'owner'
  },

  goToEdit() {
    wx.navigateTo({ url: `/pages/organization/create/index?id=${this.data.orgId}` })
  },

  /** 打开邀请弹窗 */
  openInviteModal() {
    if (!this.isOwner()) {
      wx.showToast({ title: '无权限邀请成员', icon: 'none' })
      return
    }
    this.setData({
      showInviteModal: true,
      inviteForm: { email: '', phone: '', message: '' },
    })
  },

  closeInviteModal() {
    this.setData({ showInviteModal: false })
  },

  stopPropagation() {},

  onInviteInput(e) {
    const { field } = e.currentTarget.dataset
    this.setData({
      [`inviteForm.${field}`]: e.detail.value,
    })
  },

  async handleInvite() {
    const { inviteForm, orgId } = this.data
    if (!inviteForm.email && !inviteForm.phone) {
      wx.showToast({ title: '邮箱或手机号至少填一项', icon: 'none' })
      return
    }
    this.setData({ inviting: true })
    try {
      await organizationApi.createInvite(orgId, inviteForm)
      wx.showToast({ title: '邀请已发送', icon: 'success' })
      this.closeInviteModal()
      this.fetchInvites()
    } catch (err) {
      wx.showToast({ title: err.message || '邀请失败', icon: 'none' })
    } finally {
      this.setData({ inviting: false })
    }
  },

  /** 移除成员 */
  async removeMember(e) {
    const { userId, name } = e.currentTarget.dataset
    if (!this.isOwner()) {
      wx.showToast({ title: '无权限', icon: 'none' })
      return
    }
    const res = await new Promise(resolve => {
      wx.showModal({ title: '确认移除', content: `确定将 ${name || '该成员'} 移出组织？`, success: resolve })
    })
    if (res.confirm) {
      try {
        await organizationApi.removeMember(this.data.orgId, userId)
        wx.showToast({ title: '已移除', icon: 'success' })
        this.fetchMembers()
      } catch (err) {
        wx.showToast({ title: err.message || '移除失败', icon: 'none' })
      }
    }
  },

  /** 删除组织 */
  async deleteOrg() {
    if (!this.isOwner()) {
      wx.showToast({ title: '仅组织所有者可删除', icon: 'none' })
      return
    }
    const res = await new Promise(resolve => {
      wx.showModal({ title: '确认删除', content: `确定删除「${this.data.organization.name}」？此操作不可恢复。`, success: resolve })
    })
    if (res.confirm) {
      try {
        await organizationApi.delete(this.data.orgId)
        wx.showToast({ title: '已删除', icon: 'success' })
        wx.navigateBack()
      } catch (err) {
        wx.showToast({ title: err.message || '删除失败', icon: 'none' })
      }
    }
  },

  getRoleLabel(role) {
    const labels = {
      owner: { label: '所有者', color: '#f59e0b' },
      admin: { label: '管理员', color: '#8b5cf6' },
      member: { label: '成员', color: '#22c55e' },
    }
    return labels[role] || { label: role, color: '#999' }
  },

  getInitial(name) {
    return (name || '?')[0]
  },
})
