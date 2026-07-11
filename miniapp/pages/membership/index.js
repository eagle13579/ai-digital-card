const MockService = require('../../utils/mockService')

const { getLevelText } = require('../../utils/levels')

const MEMBERSHIP_LEVELS = [
  {
    id: 'free',
    name: 'Free',
    price: '免费',
    popular: false,
    features: ['1张名片', 'OCR 3次/月', '5位访客追踪', '基础模板'],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '¥9.9/月',
    popular: true,
    features: ['10张名片', 'OCR 100次/月', '无限访客追踪', '高级模板'],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: '¥29.9/月',
    popular: false,
    features: ['无限名片', '无限OCR', '优先匹配', '专属客服'],
  },
]

Page({
  data: {
    currentLevel: 'Free',
    currentLevelId: 'free',
    levels: MEMBERSHIP_LEVELS,
  },

  onLoad() {
    this.loadUserLevel()
  },

  async loadUserLevel() {
    const profile = await MockService.getUserProfile() || {}
    const levelId = (profile && profile.memberLevel) || 'free'
    const levelText = getLevelText(levelId)
    
    this.setData({
      currentLevel: levelText,
      currentLevelId: levelId,
    })
  },

  upgrade(e) {
    const levelId = e.currentTarget.dataset.id
    
    if (levelId === this.data.currentLevelId) {
      wx.showToast({ title: '已是当前等级', icon: 'none' })
      return
    }

    const level = MEMBERSHIP_LEVELS.find(l => l.id === levelId)
    
    wx.showModal({
      title: `升级到${level.name}`,
      content: `价格：${level.price}\n\n权益：\n${level.features.join('\n')}`,
      confirmText: '确认升级',
      confirmColor: '#8b5cf6',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '支付中...' })
          setTimeout(() => {
            wx.hideLoading()
            wx.showToast({ title: '升级成功', icon: 'success' })
            this.setData({
              currentLevel: level.name,
              currentLevelId: levelId,
            })
            const store = require('../../utils/store')
            store.updateMemberLevel(levelId)
          }, 1500)
        }
      },
    })
  },
})