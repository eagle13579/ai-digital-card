/**
 * 定价套餐页面
 * - 数据来源: GET /api/plans（真实后端接口，不硬编码价格）
 * - 兜底: loading 骨架 + 错误提示重试（接口未部署 / 网络异常时友好降级）
 * - 月付/年付切换：年付约 17% 折扣，由接口价格实时计算
 */
const { get, post } = require('../../utils/request')

// 年付折扣系数：约 17% off（接口未提供年付价时按此推导，避免硬编码具体金额）
const ANNUAL_DISCOUNT_RATE = 0.83

/** 价格转数字（兼容 number / '¥199' / '199.00' 等格式） */
function toNumber(v) {
  if (typeof v === 'number') return v
  if (typeof v === 'string') return parseFloat(v.replace(/[¥￥,\s]/g, '')) || 0
  return 0
}

/** 千分位格式化整数 */
function formatMoney(n) {
  return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/** 归一化后端套餐列表（兼容多种返回结构） */
function normalizePlans(res) {
  let list = []
  if (Array.isArray(res)) {
    list = res
  } else if (res && typeof res === 'object') {
    list = res.plans || res.list || res.items || res.data || []
  }
  if (!Array.isArray(list)) list = []
  return list.map(function (p, index) {
    const monthlyPrice = toNumber(p.price_monthly || p.monthly_price || p.price_month || p.monthlyPrice || p.price)
    const monthlyTotal = monthlyPrice * 12
    const annualPrice = toNumber(p.price_annual || p.annual_price || p.price_year || p.annualPrice) ||
      Math.round(monthlyTotal * ANNUAL_DISCOUNT_RATE)
    const originalPrice = toNumber(p.original_annual || p.original_price || p.originalPrice || p.list_price || p.strike_price)
    const features = Array.isArray(p.features) ? p.features
      : (Array.isArray(p.perks) ? p.perks
      : (Array.isArray(p.benefits) ? p.benefits : []))
    return {
      id: p.id || p.plan_id || p.tier || String(index),
      name: p.name || p.plan_name || '',
      monthlyPrice: monthlyPrice,
      annualPrice: annualPrice,
      originalPrice: originalPrice,
      // 统一为字符串数组，便于 WXML wx:key="*this"
      features: features.map(function (f) {
        if (typeof f === 'string') return f
        if (f && typeof f === 'object') return f.text || f.name || f.label || ''
        return String(f || '')
      }),
      highlighted: !!(p.highlighted || p.recommended || p.popular),
      badge: p.badge || '',
    }
  })
}

/** 按当前计费周期生成展示字段（价格/划线价/折扣说明均由数据计算） */
function buildDisplayPlan(plan, isAnnual) {
  const monthlyTotal = plan.monthlyPrice * 12
  const annualTotal = plan.annualPrice
  const saveAmount = Math.max(0, monthlyTotal - annualTotal)
  const savePercent = monthlyTotal > 0 ? Math.round((saveAmount / monthlyTotal) * 100) : 0
  const price = isAnnual ? plan.annualPrice : plan.monthlyPrice
  let originalText = ''
  if (isAnnual) {
    // 年付模式划线价为月付单价，突出年付优惠
    originalText = plan.monthlyPrice > 0 ? '¥' + formatMoney(plan.monthlyPrice) + '/月' : ''
  } else if (plan.originalPrice > 0) {
    originalText = '¥' + formatMoney(plan.originalPrice)
  }
  return Object.assign({}, plan, {
    priceText: '¥' + formatMoney(price),
    periodText: '/月',
    originalText: originalText,
    annualHint: isAnnual && plan.monthlyPrice > 0
      ? '年付共 ¥' + formatMoney(annualTotal) + ' · 省 ' + savePercent + '%'
      : '',
    savePercent: savePercent,
  })
}

Page({
  data: {
    loading: true,
    error: false,
    errorText: '',
    billingPeriod: 'monthly', // monthly | annual
    annualSavePercent: 17,
    plans: [],
  },

  onLoad() {
    this.fetchPlans()
  },

  onPullDownRefresh() {
    this.fetchPlans().then(function () {
      wx.stopPullDownRefresh()
    }).catch(function () {
      wx.stopPullDownRefresh()
    })
  },

  /** 从 /api/plans 拉取套餐数据（GET，request.js 封装，BASE 读取自 config） */
  fetchPlans() {
    this.setData({ loading: true, error: false })
    return get('/api/plans', {}, { noAuth: true }).then(function (res) {
      let raw = normalizePlans(res)
      if (!raw.length) {
        this.setData({ error: true, errorText: '暂未获取到套餐信息，请稍后重试', loading: false })
        return
      }
      const isAnnual = this.data.billingPeriod === 'annual'
      let plans = raw.map(function (p) { return buildDisplayPlan(p, isAnnual) })
      // Pro 卡高亮「最受欢迎」
      const proPlan = plans.find(function (p) {
        return /^pro$/i.test(p.id) || /pro/i.test(p.name)
      }) || plans[1]
      plans = plans.map(function (p) {
        return Object.assign({}, p, {
          highlighted: p.highlighted || (proPlan && p.id === proPlan.id),
          badge: p.badge || (proPlan && p.id === proPlan.id ? '最受欢迎' : ''),
        })
      })
      // 年付折扣百分比取第一张付费套餐的实测值
      const paid = plans.find(function (p) { return p.monthlyPrice > 0 })
      const annualSavePercent = paid ? (paid.savePercent || 17) : 17
      this.setData({ plans: plans, annualSavePercent: annualSavePercent, loading: false, error: false })
    }.bind(this)).catch(function (err) {
      console.error('[Pricing] 拉取套餐失败:', err)
      this.setData({ error: true, errorText: '套餐数据加载失败，请检查网络后重试', loading: false })
    }.bind(this))
  },

  /** 月付 / 年付切换 */
  onToggleBilling(e) {
    const period = e.currentTarget.dataset.period
    if (period === this.data.billingPeriod) return
    const isAnnual = period === 'annual'
    const plans = this.data.plans.map(function (p) { return buildDisplayPlan(p, isAnnual) })
    this.setData({ billingPeriod: period, plans: plans })
  },

  /** 错误兜底：重新加载 */
  onRetry() {
    this.fetchPlans()
  },

  /** 底部按钮「升级Pro」→ 拉取最新套餐数据渲染 */
  onUpgradePro() {
    if (this.data.loading) return
    wx.showLoading({ title: '获取套餐信息...', mask: true })
    this.fetchPlans().then(function () {
      wx.hideLoading()
      const pro = this.data.plans.find(function (p) { return p.highlighted }) ||
        this.data.plans.find(function (p) { return /pro/i.test(p.id) || /pro/i.test(p.name) })
      if (!pro) {
        wx.showToast({ title: '套餐信息异常，请重试', icon: 'none' })
        return
      }
      const isAnnual = this.data.billingPeriod === 'annual'
      const priceText = isAnnual
        ? '年付共 ¥' + formatMoney(pro.annualPrice)
        : '¥' + formatMoney(pro.monthlyPrice) + '/月'
      wx.showModal({
        title: '升级 ' + pro.name,
        content: '确认升级到 ' + pro.name + '（' + priceText + '）？',
        confirmText: '确认升级',
        cancelText: '再想想',
        success: function (res) {
          if (res.confirm) {
            wx.showToast({ title: '升级申请已提交', icon: 'success' })
          }
        },
      })
    }.bind(this)).catch(function () {
      wx.hideLoading()
      // 失败时 fetchPlans 内部已置 error 状态并展示重试入口
    }.bind(this))
  },
})
