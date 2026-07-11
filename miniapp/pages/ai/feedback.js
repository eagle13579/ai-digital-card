/**
 * 反馈收集 - 用户反馈提交与历史列表
 * 支持 MockService 数据源 (useRealApi 开关)
 */
const MockService = require('../../../utils/mockService')

const FEEDBACK_TYPES = [
  { value: 'bug', label: '🐛 问题反馈' },
  { value: 'feature', label: '💡 功能建议' },
  { value: 'improve', label: '✨ 体验优化' },
  { value: 'other', label: '📝 其他' },
]

const MOCK_HISTORY = [
  { id: 'fb_001', type: 'bug', title: '名片编辑保存失败', content: '编辑名片时点击保存按钮无响应，需退出重试', status: 'resolved', createdAt: '2026-07-10', reply: '已修复，请更新到最新版本' },
  { id: 'fb_002', type: 'feature', title: '希望增加批量导入功能', content: '目前只能逐条添加联系人，希望能支持Excel批量导入', status: 'pending', createdAt: '2026-07-08', reply: '' },
  { id: 'fb_003', type: 'improve', title: 'AI对话响应速度优化', content: 'AI对话在复杂问题时响应较慢，建议增加流式输出', status: 'reviewing', createdAt: '2026-07-05', reply: '已列入下一版优化计划' },
  { id: 'fb_004', type: 'other', title: '合作咨询', content: '希望与贵公司建立商务合作，请与我联系', status: 'resolved', createdAt: '2026-06-28', reply: '已转交商务团队跟进' },
]

Page({
  data: {
    useRealApi: false,
    loading: true,
    feedbackTypes: FEEDBACK_TYPES,
    // 当前tab
    currentTab: 'submit', // submit | history
    // 提交表单
    selectedType: 0,
    title: '',
    content: '',
    submitting: false,
    // 历史列表
    history: [],
    historyLoading: false,
  },

  async onLoad() {
    await this.loadHistory()
  },

  async loadHistory() {
    this.setData({ historyLoading: true })
    try {
      if (this.data.useRealApi) {
        // TODO: 对接真实API
        await new Promise(r => setTimeout(r, 500))
      } else {
        await new Promise(r => setTimeout(r, 400))
      }
      this.setData({ history: MOCK_HISTORY, loading: false, historyLoading: false })
    } catch (e) {
      console.error('[Feedback] 加载历史失败:', e)
      this.setData({ loading: false, historyLoading: false })
    }
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ currentTab: tab })
  },

  onTypeChange(e) {
    this.setData({ selectedType: e.detail.value })
  },

  onTitleInput(e) {
    this.setData({ title: e.detail.value })
  },

  onContentInput(e) {
    this.setData({ content: e.detail.value })
  },

  async submitFeedback() {
    const { selectedType, title, content, feedbackTypes } = this.data

    if (!title.trim()) {
      wx.showToast({ title: '请输入标题', icon: 'none' })
      return
    }
    if (!content.trim()) {
      wx.showToast({ title: '请输入反馈内容', icon: 'none' })
      return
    }
    if (content.trim().length < 5) {
      wx.showToast({ title: '反馈内容至少5个字', icon: 'none' })
      return
    }

    this.setData({ submitting: true })
    try {
      if (this.data.useRealApi) {
        // TODO: 对接真实API
        await new Promise(r => setTimeout(r, 1000))
      } else {
        await new Promise(r => setTimeout(r, 800))
      }

      const newFeedback = {
        id: `fb_${Date.now()}`,
        type: feedbackTypes[selectedType].value,
        title: title.trim(),
        content: content.trim(),
        status: 'pending',
        createdAt: new Date().toISOString().slice(0, 10),
        reply: '',
      }

      wx.showToast({ title: '提交成功', icon: 'success' })
      this.setData({
        history: [newFeedback, ...this.data.history],
        selectedType: 0,
        title: '',
        content: '',
        submitting: false,
        currentTab: 'history',
      })
    } catch (e) {
      console.error('[Feedback] 提交失败:', e)
      wx.showToast({ title: '提交失败，请重试', icon: 'none' })
      this.setData({ submitting: false })
    }
  },

  getStatusText(status) {
    const map = { pending: '待处理', reviewing: '处理中', resolved: '已解决', closed: '已关闭' }
    return map[status] || status
  },

  getStatusColor(status) {
    const map = { pending: '#F59E0B', reviewing: '#0EA5E9', resolved: '#22C55E', closed: '#9CA3AF' }
    return map[status] || '#9CA3AF'
  },

  getTypeLabel(typeVal) {
    const map = { bug: '🐛 问题', feature: '💡 建议', improve: '✨ 优化', other: '📝 其他' }
    return map[typeVal] || typeVal
  },

  onShareAppMessage() {
    return {
      title: '反馈建议 - AI数智名片',
      path: '/pages/ai/feedback',
    }
  },
})
