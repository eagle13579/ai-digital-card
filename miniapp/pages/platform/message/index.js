const { messageApi } = require('../../../utils/api')

Page({
  data: {
    loading: false,
    activeTab: 'send',       // 'send' | 'list'
    // 发布消息
    receiverIndex: -1,
    receiverOptions: [],
    messageContent: '',
    sending: false,
    // 消息列表
    conversations: [],
    unreadCount: 0,
  },

  onLoad() {
    this.loadReceiverOptions()
    this.loadUnreadCount()
    this.loadConversations()
  },

  onShow() {
    this.loadUnreadCount()
    this.loadConversations()
  },

  /** 返回上一页 */
  goBack() {
    wx.navigateBack()
  },

  /** 切换到发布消息 */
  switchToSend() {
    this.setData({ activeTab: 'send' })
  },

  /** 切换到消息列表 */
  switchToList() {
    this.setData({ activeTab: 'list' })
    this.loadConversations()
  },

  /** 加载接收人选项（从平台成员数据） */
  loadReceiverOptions() {
    const eventChannel = this.getOpenerEventChannel()
    // 尝试从上一页获取平台成员列表
    try {
      const pages = getCurrentPages()
      const prevPage = pages[pages.length - 2]
      if (prevPage && prevPage.data && prevPage.data.members) {
        const members = prevPage.data.members || []
        const options = members.map(m => ({
          value: m.user_id || m.id,
          label: m.name || m.user_name || '未知用户',
        }))
        this.setData({ receiverOptions: options })
        return
      }
    } catch (e) {
      // 降级: 通过 API 获取平台成员（模拟）
    }
    // 如果获取不到则设为空，发送时再要求选择
  },

  /** 接收人选择变化 */
  onReceiverChange(e) {
    this.setData({ receiverIndex: e.detail.value })
  },

  /** 消息内容输入 */
  onContentInput(e) {
    this.setData({ messageContent: e.detail.value })
  },

  /** 是否可发送 */
  get canSend() {
    return this.data.receiverIndex >= 0 && this.data.messageContent.trim().length > 0 && !this.data.sending
  },

  /** 发送消息 — 使用 messageApi（自动注入 Bearer Token） */
  async sendMessage() {
    if (!this.canSend) return
    const { receiverOptions, receiverIndex, messageContent } = this.data
    const receiver = receiverOptions[receiverIndex]
    if (!receiver) {
      wx.showToast({ title: '请选择接收人', icon: 'none' })
      return
    }

    this.setData({ sending: true })
    try {
      const res = await messageApi.sendMessage(receiver.value, messageContent.trim())

      wx.showToast({ title: '发送成功', icon: 'success' })
      this.setData({
        messageContent: '',
        receiverIndex: -1,
        sending: false,
      })
      // 切换到消息列表查看
      this.loadConversations()
    } catch (err) {
      console.error('[MessageSend] 发送消息失败:', err)
      wx.showToast({ title: err.message || '网络错误，请重试', icon: 'none' })
      this.setData({ sending: false })
    }
  },

  /** 加载未读数 — 使用 messageApi */
  async loadUnreadCount() {
    try {
      const data = await messageApi.getUnreadCount()
      this.setData({ unreadCount: data?.count || data || 0 })
    } catch (err) {
      console.warn('[Message] 加载未读数失败:', err)
    }
  },

  /** 加载会话列表 — 使用 messageApi */
  async loadConversations() {
    this.setData({ loading: true })
    try {
      const convs = await messageApi.listConversations()
      this.setData({ conversations: convs || [] })
    } catch (err) {
      console.warn('[Message] 加载会话列表失败:', err)
      this.setData({ conversations: [] })
    } finally {
      this.setData({ loading: false })
    }
  },

  /** 刷新列表 */
  refreshList() {
    this.loadUnreadCount()
    this.loadConversations()
    wx.showToast({ title: '已刷新', icon: 'success' })
  },

  /** 打开会话详情 */
  openConversation(e) {
    const convId = e.currentTarget.dataset.id
    if (convId) {
      wx.navigateTo({
        url: `/pages/message/chat/index?conversation_id=${convId}`,
      })
    }
  },
})
