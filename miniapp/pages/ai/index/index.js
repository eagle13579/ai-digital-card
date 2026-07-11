const features = [
  { id: 'chat', name: 'AI智能对话', icon: '🤖', desc: '基础问答/深度推理', url: '/pages/ai/chat/index' },
  { id: 'generate', name: 'AI内容生成', icon: '✍️', desc: '自我介绍/口号/介绍信', url: '/pages/ai/generate/index' },
  { id: 'scan', name: 'AI名片扫描', icon: '📸', desc: '拍照识别名片信息', url: '/pages/ai/scan/index' },
  { id: 'match', name: '智能人脉匹配', icon: '🎯', desc: '筛选推荐合作伙伴', url: '/pages/ai/match/index' },
  { id: 'insight', name: 'AI数据洞察', icon: '📊', desc: '访客趋势分析报告', url: '/pages/ai/insight/index' },
  { id: 'config', name: 'AI客服配置', icon: '⚙️', desc: '自动回复/欢迎语设置', url: '/pages/ai/config/index' },
]

Page({
  data: {
    features,
    isLoggedIn: false,
  },

  onLoad() {
    const app = getApp()
    this.setData({ isLoggedIn: app.isLoggedIn() })
  },

  go(e) {
    const app = getApp()
    if (!app.isLoggedIn()) {
      return wx.showToast({ title: '请先登录', icon: 'none' })
    }
    const url = e.currentTarget.dataset.url
    wx.navigateTo({ url })
  },

  goLogin() {
    wx.navigateTo({ url: '/pages/login/index' })
  },

  onShareAppMessage() {
    return {
      title: 'AI数智名片 - AI智能中心',
      path: '/pages/ai/index/index',
      imageUrl: '',
    }
  },
})