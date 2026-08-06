/**
 * 会员中心页面
 */
const { MockService } = require('../../utils/mockService')

Page({
  data: {
    loading: true,
    currentLevel: 'free',
    currentLevelText: 'Free',
    expireDate: '',
    plans: [
      {
        id: 'free',
        name: 'Free',
        price: '¥0',
        period: '永续',
        color: '#999',
        features: ['1张名片', 'OCR 3次/月', '5位访客追踪', '基础模板'],
        highlighted: false,
        badge: '',
      },
      {
        id: 'pro',
        name: 'Pro',
        price: '¥99',
        period: '/月',
        originalPrice: '¥199',
        color: '#f5a623',
        features: ['无限名片', 'OCR 1000次/月', '实时访客Push', 'AI分析仪表盘', '智能人脉匹配', '去水印'],
        highlighted: true,
        badge: '推荐',
      },
      {
        id: 'enterprise',
        name: 'Enterprise',
        price: '¥499',
        period: '/月',
        color: '#667eea',
        features: ['无限名片+OCR', '批量导入(≤50人)', 'SSO+RBAC', '团队协作', '专属客服', 'API接入', '自定义品牌'],
        highlighted: false,
        badge: '',
      },
    ],
    // 功能对比表
    featureComparison: [
      { feature: '名片创建', free: '1张', pro: '无限', enterprise: '无限' },
      { feature: 'OCR识别', free: '3次/月', pro: '1000次/月', enterprise: '无限' },
      { feature: '访客追踪', free: '5位', pro: '无限', enterprise: '无限' },
      { feature: '实时Push通知', free: '—', pro: '✓', enterprise: '✓' },
      { feature: 'AI分析仪表盘', free: '—', pro: '✓', enterprise: '✓' },
      { feature: '智能人脉匹配', free: '—', pro: '✓', enterprise: '✓' },
      { feature: '批量导入', free: '—', pro: '500人', enterprise: '无限' },
      { feature: '团队协作', free: '—', pro: '—', enterprise: '✓' },
      { feature: 'SSO+RBAC', free: '—', pro: '—', enterprise: '✓' },
      { feature: 'API接入', free: '100次/月', pro: '5000次/月', enterprise: '无限' },
    ],
    // 使用额度
    usage: {
      card_count: 0,
      card_limit: 1,
      ocr_count: 0,
      ocr_limit: 3,
      visitor_count: 0,
    },
  },

  onLoad() {
    this.loadMembershipData()
  },

  onShow() {
    if (!this.data.loading) {
      this.loadMembershipData()
    }
  },

  async loadMembershipData() {
    this.setData({ loading: true })
    try {
      const [statusRes, usageRes] = await Promise.all([
        MockService.getMembershipStatus(),
        MockService.getMembershipUsage(),
      ])

      const status = statusRes.data !== undefined ? statusRes.data : statusRes
      const usage = usageRes.data !== undefined ? usageRes.data : usageRes

      const memberLevel = status.tier || status.level || 'free'
      const levelTextMap = { free: 'Free', pro: 'Pro', enterprise: 'Enterprise' }
      const currentLevelText = levelTextMap[memberLevel] || 'Free'

      const plans = this.data.plans.map(p => ({
        ...p,
        highlighted: p.id === memberLevel || (p.id === 'pro' && memberLevel === 'free'),
        badge: p.id === memberLevel ? '当前' : (p.id === 'pro' ? '推荐' : ''),
      }))

      this.setData({
        currentLevel: memberLevel,
        currentLevelText,
        expireDate: status.expire_at || status.expire_date || '',
        plans,
        usage: {
          card_count: usage.card_count || usage.cardCount || 0,
          card_limit: usage.card_limit || usage.cardLimit || (memberLevel === 'free' ? 1 : 10),
          ocr_count: usage.ocr_count || usage.ocrCount || 0,
          ocr_limit: usage.ocr_limit || usage.ocrLimit || (memberLevel === 'free' ? 3 : 100),
          visitor_count: usage.visitor_count || usage.visitorCount || 0,
        },
        loading: false,
      })
    } catch (err) {
      console.error('加载会员数据失败:', err)
      this.setData({ loading: false })
    }
  },

  // 选择套餐
  selectPlan(e) {
    const planId = e.currentTarget.dataset.plan
    if (planId === 'free') {
      wx.showToast({ title: '当前为免费版', icon: 'none' })
      return
    }
    if (planId === this.data.currentLevel) {
      wx.showToast({ title: '已是当前套餐', icon: 'none' })
      return
    }
    this.doUpgrade(planId)
  },

  async doUpgrade(planId) {
    wx.showLoading({ title: '处理中...', mask: true })
    try {
      const res = await MockService.membershipUpgrade(planId, 'monthly')
      wx.hideLoading()
      if (res && res.pay_params) {
        const pay = res.pay_params
        const app = getApp()
        wx.requestPayment({
          timeStamp: pay.timeStamp || String(Math.floor(Date.now() / 1000)),
          nonceStr: pay.nonceStr || 'mock_nonce',
          package: pay.package || 'prepay_id=mock',
          signType: pay.signType || 'RSA',
          paySign: pay.paySign || 'mock_sign',
          success: () => {
            wx.showToast({ title: '支付成功', icon: 'success' })
            this.loadMembershipData()
            if (typeof app.updateMemberLevel === 'function') {
              app.updateMemberLevel(planId)
            }
          },
          fail: (err) => {
            if (err.errMsg && err.errMsg.indexOf('cancel') > -1) {
              wx.showToast({ title: '已取消支付', icon: 'none' })
            } else {
              wx.showToast({ title: '支付失败，请重试', icon: 'none' })
              console.error('支付失败:', err)
            }
          },
        })
      } else {
        wx.showToast({ title: '升级成功', icon: 'success' })
        this.loadMembershipData()
        const app = getApp()
        if (typeof app.updateMemberLevel === 'function') {
          app.updateMemberLevel(planId)
        }
      }
    } catch (err) {
      wx.hideLoading()
      console.error('升级失败:', err)
      wx.showToast({ title: '升级失败，请重试', icon: 'none' })
    }
  },
})
