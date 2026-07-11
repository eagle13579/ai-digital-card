/**
 * AI数据洞察 - 带趋势图
 */
const MockService = require('../../../utils/mockService')
Page({
  data: { stats: null, loading: true, weeklyTrend: [] },
  async onLoad() {
    try {
      const insightData = await MockService.getInsightData()
      const stats = insightData.visits || insightData
      this.setData({
        stats,
        weeklyTrend: stats.weeklyTrend || [],
        loading: false,
      }, () => {
        this.drawChart()
      })
    } catch (e) {
      console.error('获取数据洞察失败:', e)
      this.setData({ loading: false })
    }
  },

  onReady() {
    // 确保canvas已渲染后再绘制
    setTimeout(() => this.drawChart(), 300)
  },

  drawChart() {
    const trend = this.data.weeklyTrend
    if (!trend || trend.length === 0) return

    const query = wx.createSelectorQuery()
    query.select('#trendCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res || !res[0]) return
        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        const dpr = wx.getSystemInfoSync().pixelRatio
        const width = res[0].width
        const height = res[0].height
        canvas.width = width * dpr
        canvas.height = height * dpr
        ctx.scale(dpr, dpr)

        const padding = { top: 20, bottom: 30, left: 30, right: 20 }
        const chartW = width - padding.left - padding.right
        const chartH = height - padding.top - padding.bottom
        const barCount = trend.length
        const barGap = 8
        const barW = (chartW - barGap * (barCount - 1)) / barCount
        const maxVal = Math.max(...trend, 1)

        // Clear
        ctx.clearRect(0, 0, width, height)

        // Draw grid lines
        ctx.strokeStyle = 'rgba(0,0,0,0.06)'
        ctx.lineWidth = 1
        for (let i = 0; i <= 4; i++) {
          const y = padding.top + (chartH / 4) * i
          ctx.beginPath()
          ctx.moveTo(padding.left, y)
          ctx.lineTo(width - padding.right, y)
          ctx.stroke()

          // Y-axis label
          const val = Math.round(maxVal - (maxVal / 4) * i)
          ctx.fillStyle = '#999'
          ctx.font = '10px sans-serif'
          ctx.textAlign = 'right'
          ctx.fillText(String(val), padding.left - 6, y + 4)
        }

        // Draw bars
        const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        const colors = ['#1657ff', '#1657ff', '#1657ff', '#1657ff', '#1657ff', '#f59e0b', '#f59e0b']

        trend.forEach((val, i) => {
          const barH = (val / maxVal) * chartH
          const x = padding.left + i * (barW + barGap)
          const y = padding.top + chartH - barH

          // Bar
          const gradient = ctx.createLinearGradient(x, y, x, padding.top + chartH)
          gradient.addColorStop(0, colors[i % colors.length])
          gradient.addColorStop(1, colors[i % colors.length] + '33')
          ctx.fillStyle = gradient
          ctx.beginPath()
          ctx.roundRect ? ctx.roundRect(x, y, barW, barH, 4) : ctx.rect(x, y, barW, barH)
          ctx.fill()

          // Value on top
          ctx.fillStyle = '#1a1a1a'
          ctx.font = '11px sans-serif'
          ctx.textAlign = 'center'
          ctx.fillText(String(val), x + barW / 2, y - 6)

          // Day label below
          const dayIndex = trend.length === 7 ? i : i
          ctx.fillStyle = '#999'
          ctx.font = '10px sans-serif'
          ctx.textAlign = 'center'
          ctx.fillText(weekDays[dayIndex] || `D${i + 1}`, x + barW / 2, padding.top + chartH + 16)
        })

        // Title
        ctx.fillStyle = '#666'
        ctx.font = '12px sans-serif'
        ctx.textAlign = 'left'
        ctx.fillText('近7日访问趋势', padding.left, 14)
      })
  },
})
