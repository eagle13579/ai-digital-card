/**
 * 聊天详情页 - 消息气泡 + 底部输入框
 * 轮询每5s拉取新消息
 */
const { messageApi } = require('../../../utils/api')
const store = require('../../../utils/store')

Page({
  data: {
    conversationId: '',
    otherUserId: 0,
    otherUserName: '',
    otherAvatar: '',
    myUserId: 0,
    myAvatar: '',
    messages: [],
    inputValue: '',
    sendDisabled: true,
    page: 1,
    pageSize: 50,
    hasMoreHistory: true,
    loadingMore: false,
    scrollToId: '',
    defaultAvatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20person%20portrait%20headshot%20clean%20white%20background&image_size=square',
  },

  onLoad(options) {
    const { conversation_id, other_user_id, other_user_name } = options
    const state = store.getState()
    const userInfo = state.userInfo || {}

    this.setData({
      conversationId: conversation_id || '',
      otherUserId: parseInt(other_user_id) || 0,
      otherUserName: decodeURIComponent(other_user_name || ''),
      otherAvatar: userInfo.avatar || this.data.defaultAvatar,
      myUserId: userInfo.id || 0,
    })

    if (conversation_id) {
      this._loadMessages()
    }

    // 标记已读
    if (conversation_id) {
      messageApi.markAsRead(conversation_id).catch(() => {})
    }
  },

  onShow() {
    this._startPolling()
  },

  onHide() {
    this._stopPolling()
  },

  onUnload() {
    this._stopPolling()
  },

  /** 开始轮询（每5秒） */
  _startPolling() {
    this._stopPolling()
    this._pollTimer = setInterval(() => {
      this._pollNewMessages()
    }, 5000)
  },

  /** 停止轮询 */
  _stopPolling() {
    if (this._pollTimer) {
      clearInterval(this._pollTimer)
      this._pollTimer = null
    }
  },

  /** 轮询新消息 */
  async _pollNewMessages() {
    if (!this.data.conversationId) return
    try {
      const res = await messageApi.getMessages(this.data.conversationId, 1, 10)
      const data = res && res.messages ? res : (res?.data || res || {})
      const newMsgs = data.messages || []

      if (newMsgs.length === 0) return

      const existingIds = new Set(this.data.messages.map(m => m.id))
      const freshMsgs = newMsgs.filter(m => !existingIds.has(m.id))

      if (freshMsgs.length > 0) {
        this.setData({
          messages: [...this.data.messages, ...freshMsgs],
        })
        this._scrollToBottom()
      }
    } catch (err) {
      // 静默失败
    }
  },

  /** 加载消息 */
  async _loadMessages() {
    try {
      const res = await messageApi.getMessages(this.data.conversationId, 1, this.data.pageSize)
      const data = res && res.messages ? res : (res?.data || res || {})
      const messages = data.messages || []
      const total = data.total || 0

      this.setData({
        messages,
        page: 1,
        hasMoreHistory: messages.length < total,
      })

      // 滚动到底部
      setTimeout(() => this._scrollToBottom(), 100)
    } catch (err) {
      console.error('[Chat] 加载消息失败:', err)
      wx.showToast({ title: '加载消息失败', icon: 'none' })
    }
  },

  /** 加载更多历史消息（上滚动触发） */
  async onLoadMore() {
    if (this.data.loadingMore || !this.data.hasMoreHistory) return
    this.setData({ loadingMore: true })

    const nextPage = this.data.page + 1
    try {
      const res = await messageApi.getMessages(this.data.conversationId, nextPage, this.data.pageSize)
      const data = res && res.messages ? res : (res?.data || res || {})
      const oldMsgs = data.messages || []
      const total = data.total || 0

      this.setData({
        messages: [...oldMsgs, ...this.data.messages],
        page: nextPage,
        hasMoreHistory: this.data.messages.length + oldMsgs.length < total,
        loadingMore: false,
      })
    } catch (err) {
      console.error('[Chat] 加载历史消息失败:', err)
      this.setData({ loadingMore: false })
    }
  },

  /** 输入变化 */
  onInput(e) {
    const value = e.detail.value
    this.setData({
      inputValue: value,
      sendDisabled: !value.trim(),
    })
  },

  /** 发送消息 */
  async sendMessage() {
    const content = this.data.inputValue.trim()
    if (!content) return

    this.setData({ sendDisabled: true })

    try {
      const res = await messageApi.sendMessage(this.data.otherUserId, content)
      const msg = res && res.id ? res : (res?.data || res || {})

      if (msg.id) {
        this.setData({
          messages: [...this.data.messages, msg],
          inputValue: '',
        })
        this._scrollToBottom()
      }
    } catch (err) {
      console.error('[Chat] 发送消息失败:', err)
      wx.showToast({ title: '发送失败', icon: 'none' })
      this.setData({ sendDisabled: false })
    }
  },

  /** 滚动到底部 */
  _scrollToBottom() {
    const msgs = this.data.messages
    if (msgs.length > 0) {
      const lastMsg = msgs[msgs.length - 1]
      this.setData({ scrollToId: `msg-${lastMsg.id}` })
    }
  },

  /** 是否显示时间 */
  showTime(item, index) {
    if (index === 0) return true
    const prev = this.data.messages[index - 1]
    if (!prev) return true
    const diff = new Date(item.created_at) - new Date(prev.created_at)
    return diff > 300000 // 5分钟
  },

  /** 格式化时间 */
  formatTime(timeStr) {
    if (!timeStr) return ''
    try {
      const d = new Date(timeStr)
      const now = new Date()
      // 今天：显示时分
      if (d.toDateString() === now.toDateString()) {
        return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
      }
      // 昨天
      const yesterday = new Date(now)
      yesterday.setDate(yesterday.getDate() - 1)
      if (d.toDateString() === yesterday.toDateString()) {
        return `昨天 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
      }
      // 其他
      return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    } catch (e) {
      return timeStr
    }
  },

  onScroll(e) {
    // 处理滚动事件（保留接口）
  },
})