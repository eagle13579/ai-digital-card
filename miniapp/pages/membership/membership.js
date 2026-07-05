/**
 * 会员中心页面
 * 展示 MECE 三层定价方案 (Free / Pro / Enterprise)
 * 顶部: 当前层级+到期时间
 * 中间: 三种方案卡片
 * 底部: 功能对比表
 */
const { membershipApi, userApi } = require('../../utils/api')

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
        features: ['1张名片', 'OCR 3次/月', '基础访客统计', '标准模板'],
        highlighted: false,
        badge: '',
      },
      {
        id: 'pro',
        name: 'Pro',
        price: '¥49',
        period: '/月',
        originalPrice: '¥99',
        color: '#f5a623',
        features: ['10张名片', 'OCR 100次/月', '高级访客分析', 'AI智能写作', 'Pro专属模板', '去水印'],
        highlighted: true,
        badge: '推荐',
      },
      {
        id: 'enterprise',
        name: 'Enterprise',
        price: '¥199',
        period: '/月',
        color: '#667eea',
        features: ['不限名片', 'OCR不限次数', '批量导入(≤50人)', '团队协作', '专属客服', 'API接入', '自定义品牌'],
        highlighted: false,
        badge: '',
      },
    ],
    // 功能对比表
    featureComparison: [
      { feature: '名片创建数量', free: '1张', pro: '10张', enterprise: '不限' },
      { feature: 'OCR识别', free: '3次/月', pro: '100次/月', enterprise: '不限' },
      { feature: '批量导入', free: '—', pro: '—', enterprise: '≤50人' },
      { feature: '访客统计', free: '基础', pro: '高级分析', enterprise: '完整分析' },
      { feature: 'AI智能写作', free: '—', pro: '✓', enterprise: '✓' },
      { feature: 'Pro专属模板', free: '—', pro: '✓', enterprise: '✓' },
      { feature: '去水印', free: '—', pro: '✓', enterprise: '✓' },
      { feature: '团队协作', free: '—', pro: '—', enterprise: '✓' },
      { feature: '专属客服', free: '—', pro: '—', enterprise: '✓' },
      { feature: 'API接入', free: '—', pro: '—', enterprise: '✓' },
      { feature: '自定义品牌', free: '—', pro: '—', enterprise: '✓' },
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
      // 并行获取会员状态和使用统计
      const [statusRes, usageRes] = await Promise.all([
        membershipApi.getStatus().catch(() => null),
        membershipApi.getUsageStats().catch(() => null),
      ])

      const status = statusRes?.data ?? statusRes ?? {}
      const usage = usageRes?.data ?? usageRes ?? {}

      const memberLevel = status.tier || status.level || 'free'
      const levelTextMap = { free: 'Free', pro: 'Pro', enterprise: 'Enterprise' }
      const currentLevelText = levelTextMap[memberLevel] || 'Free'

      // 更新套餐卡片突出显示
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
          card_count: usage.card_count ?? usage.cardCount ?? 0,
          card_limit: usage.card_limit ?? usage.cardLimit ?? (memberLevel === 'free' ? 1 : 10),
          ocr_count: usage.ocr_count ?? usage.ocrCount ?? 0,
          ocr_limit: usage.ocr_limit ?? usage.ocrLimit ?? (memberLevel === 'free' ? 3 : 100),
          visitor_count: usage.visitor_count ?? usage.visitorCount ?? 0,
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

  // 执行升级
  async doUpgrade(planId) {
    wx.showLoading({ title: '处理中...', mask: true })
    try {
      const res = await membershipApi.upgrade(planId, 'monthly')
      wx.hideLoading()
      if (res && res.pay_params) {
        // 需要支付
        wx.showToast({ title: '跳转支付...', icon: 'none' })
        // 实际项目中调用微信支付
        console.log('支付参数:', res.pay_params)
      } else {
        wx.showToast({ title: '升级成功', icon: 'success' })
        this.loadMembershipData()
        // 更新全局会员等级
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
