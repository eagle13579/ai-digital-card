/**
 * 消息列表页 - 会话列表
 * 轮询每5s拉取新消息
 */
const { messageApi } = require('../../../utils/api')
const { userApi } = require('../../../utils/api')

Page({
  data: {
    loading: true,
    conversations: [],
    defaultAvatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20person%20portrait%20headshot%20clean%20white%20background&image_size=square',
  },

  onLoad() {
    this._loadConversations()
  },

  onShow() {
    this._loadConversations()
    // 启动轮询（每5秒刷新）
    this._startPolling()
  },

  onHide() {
    this._stopPolling()
  },

  onUnload() {
    this._stopPolling()
  },

  onPullDownRefresh() {
    this._loadConversations().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  /** 开始轮询 */
  _startPolling() {
    this._stopPolling()
    this._pollTimer = setInterval(() => {
      this._refreshConversations()
    }, 5000)
  },

  /** 停止轮询 */
  _stopPolling() {
    if (this._pollTimer) {
      clearInterval(this._pollTimer)
      this._pollTimer = null
    }
  },

  /** 静默刷新会话（不显示loading） */
  async _refreshConversations() {
    try {
      const res = await messageApi.listConversations()
      const convs = this._normalizeConvs(res)
      if (JSON.stringify(convs) !== JSON.stringify(this.data.conversations)) {
        this.setData({ conversations: convs })
      }
    } catch (err) {
      // 静默失败
    }
  },

  /** 加载会话列表 */
  async _loadConversations() {
    this.setData({ loading: true })
    try {
      const res = await messageApi.listConversations()
      const convs = this._normalizeConvs(res)
      // 获取对方的用户信息（名称/头像）
      await this._enrichConversations(convs)
      this.setData({ conversations: convs, loading: false })
    } catch (err) {
      console.error('[MessageList] 加载会话失败:', err)
      this.setData({ loading: false })
    }
  },

  /** 标准化会话数据 */
  _normalizeConvs(res) {
    let data = res
    if (res && res.data) data = res.data
    if (!Array.isArray(data)) data = []
    return data
  },

  /** 补充对方用户信息 */
  async _enrichConversations(convs) {
    for (const conv of convs) {
      if (!conv.other_user_name && conv.other_user_id) {
        try {
          const user = await userApi.getUser(conv.other_user_id)
          if (user) {
            conv.other_user_name = user.name || ''
            conv.avatar = user.avatar || ''
          }
        } catch (e) {
          conv.other_user_name = conv.other_user_name || `用户${conv.other_user_id}`
        }
      }
    }
  },

  /** 格式化时间 */
  formatTime(timeStr) {
    if (!timeStr) return ''
    try {
      const d = new Date(timeStr)
      const now = new Date()
      const diffMs = now - d

      // 今天：显示时分
      if (d.toDateString() === now.toDateString()) {
        return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
      }
      // 昨天
      const yesterday = new Date(now)
      yesterday.setDate(yesterday.getDate() - 1)
      if (d.toDateString() === yesterday.toDateString()) {
        return '昨天'
      }
      // 今年：月-日
      if (d.getFullYear() === now.getFullYear()) {
        return `${d.getMonth() + 1}/${d.getDate()}`
      }
      // 其他：年-月-日
      return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`
    } catch (e) {
      return timeStr
    }
  },

  /** 跳转聊天页 */
  goChat(e) {
    const conv = e.currentTarget.dataset.conv
    if (!conv) return
    // 标记已读
    messageApi.markAsRead(conv.conversation_id).catch(() => {})
    wx.navigateTo({
      url: `/pages/message/chat/index?conversation_id=${conv.conversation_id}&other_user_id=${conv.other_user_id}&other_user_name=${encodeURIComponent(conv.other_user_name || '')}`,
    })
  },

  /** 删除会话（长按） */
  deleteConversation(e) {
    const conv = e.currentTarget.dataset.conv
    if (!conv) return
    wx.showModal({
      title: '提示',
      content: '确定删除该会话？',
      confirmColor: '#ef4444',
      success: (res) => {
        if (res.confirm) {
          const conversations = this.data.conversations.filter(
            c => c.conversation_id !== conv.conversation_id
          )
          this.setData({ conversations })
        }
      },
    })
  },

  /** 跳转搜索 */
  goSearch() {
    wx.navigateTo({ url: '/pages/search/index' })
  },
})