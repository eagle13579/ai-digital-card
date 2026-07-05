/**
 * pages/ai/index.js
 * AI能力聚合入口页 — 展示全部AI功能卡片
 */
const features = [
  {
    id: 'chat',
    icon: '💬',
    title: 'AI智能对话',
    desc: '智能问答、文案润色、知识查询',
    path: '/pages/ai/chat/index',
    color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  {
    id: 'generate',
    icon: '✨',
    title: 'AI内容生成',
    desc: '生成名片文案、产品介绍、新闻稿',
    path: '/pages/ai/generate/index',
    color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  },
  {
    id: 'scan',
    icon: '📷',
    title: 'AI名片扫描分析',
    desc: '智能识别名片信息，自动提取联系方式',
    path: '/pages/ai/chat/index',
    color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  },
  {
    id: 'match',
    icon: '🤝',
    title: '智能人脉匹配',
    desc: '基于AI分析推荐最佳人脉连接',
    path: '/pages/ai/chat/index',
    color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  },
  {
    id: 'insight',
    icon: '📊',
    title: 'AI数据洞察',
    desc: '深度分析名片数据，发现商业趋势',
    path: '/pages/ai/chat/index',
    color: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  },
  {
    id: 'config',
    icon: '⚙️',
    title: 'AI客服配置',
    desc: '自定义智能客服回复规则与风格',
    path: '/pages/ai/chat/index',
    color: 'linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)',
  },
]

Page({
  data: {
    features,
    coreFeatures: features.slice(0, 3),
    advancedFeatures: features.slice(3, 6),
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: 'AI能力中心' })
  },

  navigateTo(e) {
    const path = e.currentTarget.dataset.path
    wx.navigateTo({ url: path })
  },
})
