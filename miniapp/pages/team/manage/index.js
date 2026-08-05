const { teamApi } = require('../../../utils/api')
const { MockService } = require('../../../utils/mockService')

const ROLE_LABELS = {
  owner: { label: '所有者', color: '#f59e0b' },
  admin: { label: '管理员', color: '#8b5cf6' },
  member: { label: '成员', color: '#22c55e' },
  viewer: { label: '观察者', color: '#6b7280' },
}

Page({
  data: {
    teamId: '',
    team: null,
    members: [],
    invites: [],
    approvalRequests: [],
    currentUserRole: 'member',
    currentUserId: '',
    loading: true,
    activeTab: 'members', // members | invites | approvals
    showInviteModal: false,
    inviteForm: { email: '', phone: '', role: 'member', message: '' },
    inviting: false,
  },

  onLoad(options) {
    const teamId = parseInt(options.id, 10)
    if (!teamId) {
      wx.showToast({ title: '参数错误', icon: 'none' })
      wx.navigateBack()
      return
    }
    this.setData({ teamId })
    this.loadData()
  },

  onShow() {
    if (this.data.teamId) {
      this.loadData()
    }
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const [team, members, invites, requests] = await Promise.all([
        this.fetchTeam(),
        this.fetchMembers(),
        this.fetchInvites(),
        this.fetchApprovalRequests(),
      ])
      const { userInfo } = require('../../../utils/store').getState()
      const currentUserId = userInfo?.id || ''
      const myMember = members.find(m => String(m.user_id) === String(currentUserId) || m.user_id === currentUserId)
      const currentUserRole = myMember?.role || 'member'
      this.setData({
        team,
        members,
        invites,
        approvalRequests: requests,
        currentUserId,
        currentUserRole,
        loading: false,
      })
    } catch (err) {
      console.error('[TeamManage] 加载失败:', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  async fetchTeam() {
    if (!MockService.USE_MOCK) {
      try {
        return await teamApi.getById(this.data.teamId)
      } catch (e) {
        console.warn('[TeamManage] 获取团队详情失败:', e)
      }
    }
    return (await MockService.mockDelay(200), {
      id: this.data.teamId,
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
      created_at: new Date().toISOString(),
    })
  },

  async fetchMembers() {
    if (!MockService.USE_MOCK) {
      try {
        return await teamApi.getMembers(this.data.teamId)
      } catch (e) {
        console.warn('[TeamManage] 获取成员列表失败:', e)
      }
    }
    await MockService.mockDelay(200)
    return [
      { id: 1, user_id: 'u001', name: '张伟', avatar: '', phone: '', company: '科技创新有限公司', title: '产品经理', role: 'owner', title_in_team: '团队负责人', joined_at: new Date().toISOString() },
      { id: 2, user_id: 'u002', name: '李娜', avatar: '', phone: '', company: '金融投资集团', title: '投资总监', role: 'admin', title_in_team: '运营主管', joined_at: new Date().toISOString() },
      { id: 3, user_id: 'u003', name: '王强', avatar: '', phone: '', company: '人工智能研究院', title: '首席技术官', role: 'member', title_in_team: '技术顾问', joined_at: new Date().toISOString() },
      { id: 4, user_id: 'u004', name: '赵丽', avatar: '', phone: '', company: '互联网公司', title: '技术总监', role: 'member', title_in_team: '开发工程师', joined_at: new Date().toISOString() },
      { id: 5, user_id: 'u005', name: '陈明', avatar: '', phone: '', company: '创业孵化平台', title: '孵化总监', role: 'member', title_in_team: '商务拓展', joined_at: new Date().toISOString() },
    ]
  },

  async fetchInvites() {
    if (!MockService.USE_MOCK) {
      try {
        return await teamApi.getInvites(this.data.teamId)
      } catch (e) {
        console.warn('[TeamManage] 获取邀请列表失败:', e)
      }
    }
    await MockService.mockDelay(200)
    return [
      { id: 1, team_id: this.data.teamId, invitee_email: 'test@example.com', invitee_phone: '', role: 'member', status: 'pending', created_at: new Date().toISOString(), inviter_id: 'u001' },
      { id: 2, team_id: this.data.teamId, invitee_email: 'newuser@example.com', invitee_phone: '', role: 'admin', status: 'pending', created_at: new Date().toISOString(), inviter_id: 'u001' },
    ]
  },

  async fetchApprovalRequests() {
    if (!MockService.USE_MOCK) {
      try {
        return await teamApi.listApprovalRequests(this.data.teamId)
      } catch (e) {
        console.warn('[TeamManage] 获取审批列表失败:', e)
      }
    }
    await MockService.mockDelay(200)
    return []
  },

  switchTab(e) {
    const { tab } = e.currentTarget.dataset
    this.setData({ activeTab: tab })
  },

  goBack() {
    wx.navigateBack()
  },

  canManage() {
    return this.data.currentUserRole === 'owner' || this.data.currentUserRole === 'admin'
  },

  /** 打开邀请弹窗 */
  openInviteModal() {
    if (!this.canManage()) {
      wx.showToast({ title: '无权限邀请成员', icon: 'none' })
      return
    }
    this.setData({
      showInviteModal: true,
      inviteForm: { email: '', phone: '', role: 'member', message: '' },
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

  onInviteRoleChange(e) {
    const roles = ['member', 'admin', 'viewer']
    this.setData({
      'inviteForm.role': roles[e.detail.value],
    })
  },

  async handleInvite() {
    const { inviteForm, teamId } = this.data
    if (!inviteForm.email && !inviteForm.phone) {
      wx.showToast({ title: '邮箱或手机号至少填一项', icon: 'none' })
      return
    }
    this.setData({ inviting: true })
    try {
      await teamApi.inviteMember(teamId, inviteForm)
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
    if (!this.canManage()) {
      wx.showToast({ title: '无权限', icon: 'none' })
      return
    }
    const res = await new Promise(resolve => {
      wx.showModal({ title: '确认移除', content: `确定将 ${name || '该成员'} 移出团队？`, success: resolve })
    })
    if (res.confirm) {
      try {
        await teamApi.removeMember(this.data.teamId, userId)
        wx.showToast({ title: '已移除', icon: 'success' })
        this.fetchMembers()
      } catch (err) {
        wx.showToast({ title: err.message || '移除失败', icon: 'none' })
      }
    }
  },

  /** 审批请求 - 通过 */
  async approveRequest(e) {
    const { reqId } = e.currentTarget.dataset
    try {
      await teamApi.reviewApprovalRequest(this.data.teamId, reqId, { action: 'approve' })
      wx.showToast({ title: '已通过', icon: 'success' })
      this.fetchApprovalRequests()
      this.fetchMembers()
    } catch (err) {
      wx.showToast({ title: err.message || '操作失败', icon: 'none' })
    }
  },

  /** 审批请求 - 拒绝 */
  async rejectRequest(e) {
    const { reqId } = e.currentTarget.dataset
    try {
      await teamApi.reviewApprovalRequest(this.data.teamId, reqId, { action: 'reject', reject_reason: '' })
      wx.showToast({ title: '已拒绝', icon: 'success' })
      this.fetchApprovalRequests()
    } catch (err) {
      wx.showToast({ title: err.message || '操作失败', icon: 'none' })
    }
  },

  getRoleLabel(role) {
    return ROLE_LABELS[role] || { label: role, color: '#999' }
  },

  getInitial(name) {
    return (name || '?')[0]
  },
})
