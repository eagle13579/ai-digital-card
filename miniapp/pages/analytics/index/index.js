/**
 * 增长看板 - Analytics Dashboard
 * AI数智名片
 * 
 * 展示用户增长漏斗、核心指标和转化率
 * 调用: GET /api/analytics/funnel
 */
const { get } = require('../../utils/request')

Page({
  data: {
    loading: true,
    // 漏斗数据
    funnel: {
      registered: 0,
      card_created: 0,
      matched_users: 0,
      connected: 0,
      active_7d: 0,
    },
    // 转化率
    conversionRates: {
      register_to_card: 0,
      card_to_match: 0,
      match_to_connect: 0,
    },
    // 各步骤相对于注册数的百分比（用于进度条宽度）
    funnelPercentages: {
      cardCreated: 0,
      match: 0,
      connect: 0,
    },
    // 整体转化率（连接数/注册数）
    overallConversionRate: 0,
  },

  onLoad() {
    this.loadFunnelData()
  },

  onPullDownRefresh() {
    this.loadFunnelData(() => {
      wx.stopPullDownRefresh()
    })
  },

  /**
   * 加载漏斗数据
   */
  async loadFunnelData(callback) {
    this.setData({ loading: true })
    try {
      const res = await get('/api/analytics/funnel')
      
      // 解析响应
      // res 可能是 { data: { funnel, conversion_rates } } 或直接是 { funnel, conversion_rates }
      const rawData = res && res.data ? res.data : res
      
      const funnel = rawData.funnel || {
        registered: 0,
        card_created: 0,
        matched_users: 0,
        connected: 0,
        active_7d: 0,
      }
      const conversionRates = rawData.conversion_rates || {
        register_to_card: 0,
        card_to_match: 0,
        match_to_connect: 0,
      }

      // 计算各步骤相对于注册数的百分比（进度条基准）
      const registered = funnel.registered || 1
      const funnelPercentages = {
        cardCreated: Math.round((funnel.card_created / registered) * 100),
        match: Math.round((funnel.matched_users / registered) * 100),
        connect: Math.round((funnel.connected / registered) * 100),
      }

      // 整体转化率
      const overallConversionRate = registered > 0
        ? ((funnel.connected / registered) * 100).toFixed(1)
        : '0.0'

      this.setData({
        funnel,
        conversionRates,
        funnelPercentages,
        overallConversionRate,
        loading: false,
      })

      if (callback) callback()
    } catch (err) {
      console.error('加载增长数据失败:', err)
      this.setData({ loading: false })
      if (callback) callback()
    }
  },

  /**
   * 格式化数字（带千分位）
   */
  formatNumber(num) {
    if (num === null || num === undefined) return '0'
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  },
})
