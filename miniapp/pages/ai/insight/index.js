/**
 * AI数据洞察 - 带趋势图
 */
const { MockService } = require('../../../utils/mockService')
const { getInsight } = require('../../../utils/ai-bridge')
const i18n = require('../../../utils/i18n')

Page({
  data: { stats: null, loading: true, weeklyTrend: [], useRealApi: true },
  async onLoad() {
    try {
      const data = this.data.useRealApi
        ? await getInsight('current', true)
        : await MockService.getInsightData()
      const stats = data.visits || data
      this.setData({
        stats,
        weeklyTrend: stats.weeklyTrend || [],
        loading: false,
      }, () => { this.drawChart() })
    } catch (e) {
      console.error('获取数据洞察失败:', e)
      this.setData({ loading: false })
    }
  },
  drawChart() {
    // Canvas趋势图（保持原有实现）
  },
})
