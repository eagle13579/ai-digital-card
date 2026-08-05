const { paymentApi, authApi } = require('../../utils/api')
const { getLevelText } = require('../../utils/levels')

// 前端会员等级 → 后端支付 tier 映射
const LEVEL_TIER_MAP = {
  pro: 'gold',
  enterprise: 'diamond',
}

const MEMBERSHIP_LEVELS = [
  {
    id: 'free',
    name: 'Free',
    price: '免费',
    popular: false,
    features: ['3张名片', 'OCR 3次/月', '5位访客追踪', '基础模板'],
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
    const store = require('../../utils/store')
    const { memberLevel } = store.getState()
    if (memberLevel && memberLevel !== 'free') {
      this.setData({ currentLevel: getLevelText(memberLevel), currentLevelId: memberLevel })
      return
    }
    // 从后端获取用户信息
    try {
      const profile = await authApi.getProfile()
      const levelId = (profile && profile.memberLevel) || 'free'
      const levelText = getLevelText(levelId)
      this.setData({
        currentLevel: levelText,
        currentLevelId: levelId,
      })
    } catch (e) {
      console.warn('[membership] loadUserLevel failed, fallback to free', e)
    }
  },

  async upgrade(e) {
    const levelId = e.currentTarget.dataset.id

    if (levelId === this.data.currentLevelId) {
      wx.showToast({ title: '已是当前等级', icon: 'none' })
      return
    }

    const level = MEMBERSHIP_LEVELS.find(l => l.id === levelId)
    const backendTier = LEVEL_TIER_MAP[levelId]

    wx.showModal({
      title: `升级到${level.name}`,
      content: `价格：${level.price}\n\n权益：\n${level.features.join('\n')}`,
      confirmText: '确认升级',
      confirmColor: '#8b5cf6',
      success: async (res) => {
        if (!res.confirm) return

        wx.showLoading({ title: '创建订单中...' })

        try {
          // 调用后端创建支付订单
          const result = await paymentApi.createOrder(backendTier, 'wechat', '')

          wx.hideLoading()

          const payInfo = result.pay_info || result

          // 沙箱模式：直接模拟支付成功
          if (payInfo.sandbox) {
            wx.showToast({ title: '🎉 升级成功（沙箱模式）', icon: 'success', duration: 2000 })
            this.setData({
              currentLevel: level.name,
              currentLevelId: levelId,
            })
            const store = require('../../utils/store')
            store.updateMemberLevel(levelId)
            return
          }

          // 真实微信支付：调起 wx.requestPayment
          wx.showLoading({ title: '支付中...' })
          wx.requestPayment({
            timeStamp: payInfo.timeStamp,
            nonceStr: payInfo.nonceStr,
            package: payInfo.package,
            signType: payInfo.signType || 'RSA',
            paySign: payInfo.paySign,
            success: () => {
              wx.hideLoading()
              wx.showToast({ title: '🎉 支付成功', icon: 'success', duration: 2000 })
              this.setData({
                currentLevel: level.name,
                currentLevelId: levelId,
              })
              const store = require('../../utils/store')
              store.updateMemberLevel(levelId)
            },
            fail: (err) => {
              wx.hideLoading()
              wx.showToast({
                title: err.errMsg && err.errMsg.includes('cancel') ? '已取消支付' : '支付失败',
                icon: 'none',
              })
            },
          })
        } catch (err) {
          wx.hideLoading()
          const errMsg = (err && (err.message || err.detail || err.errMsg)) || '创建订单失败'
          wx.showToast({ title: errMsg, icon: 'none', duration: 3000 })
        }
      },
    })
  },
})
