const store = require('../../utils/store')

const features = [
  { id: 'chat', name: 'AI智能对话', icon: '🤖', desc: '基础问答/深度推理', url: '/pages/ai/chat/index' },
  { id: 'generate', name: 'AI内容生成', icon: '✍️', desc: '自我介绍/口号/介绍信', url: '/pages/ai/generate/index' },
  { id: 'scan', name: 'AI名片扫描', icon: '📸', desc: '拍照识别+扫码交换', url: '/pages/ai/scan/index' },
  { id: 'match', name: '智能人脉匹配', icon: '🎯', desc: '筛选推荐合作伙伴', url: '/pages/ai/match/index' },
  { id: 'insight', name: 'AI数据洞察', icon: '📊', desc: '访客趋势分析报告', url: '/pages/ai/insight/index' },
  { id: 'gaia', name: '盖娅进化大脑', icon: '🧠', desc: 'AI进化状态/知识图谱', url: '/pages/ai/gaia' },
  { id: 'feedback', name: '反馈建议', icon: '💬', desc: '意见反馈/产品建议', url: '/pages/ai/feedback' },
  { id: 'config', name: 'AI客服配置', icon: '⚙️', desc: '自动回复/欢迎语设置', url: '/pages/ai/config/index' },
]

Page({
  data: { features, isLoggedIn: false },

  onLoad() {
    this.setData({ isLoggedIn: store.getState().isLoggedIn })
  },

  onShow() {
    const { isLoggedIn } = store.getState()
    if (this.data.isLoggedIn !== isLoggedIn) {
      this.setData({ isLoggedIn })
    }
  },

  go(e) {
    if (!store.checkLogin()) return
    const url = e.currentTarget.dataset.url
    wx.navigateTo({ url })
  },

  goLogin() {
    wx.navigateTo({ url: '/pages/login/index' })
  },

  onShareAppMessage() {
    return { title: 'AI数智名片 - AI智能中心', path: '/pages/ai/index/index' }
  },
})
