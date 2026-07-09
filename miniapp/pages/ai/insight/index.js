// pages/ai/insight/index.js — AI数据洞察
// 功能：AI驱动的数据分析与洞察建议（真实API + 降级模拟数据）
const { get } = require('../../../utils/request')

// ── 降级用的模拟数据 ──────────────────────────────────────────────
const FALLBACK_DATA = {
  stats: {
    cardCount: 128,
    viewCount: 3657,
    matchCount: 89
  },
  chartData: [
    { label: '周一', value: 42, height: 80 },
    { label: '周二', value: 56, height: 100 },
    { label: '周三', value: 38, height: 70 },
    { label: '周四', value: 72, height: 130 },
    { label: '周五', value: 95, height: 160 },
    { label: '周六', value: 45, height: 85 },
    { label: '周日', value: 33, height: 60 }
  ],
  insights: [
    {
      icon: '📈',
      title: '浏览高峰时段',
      desc: '您的名片在周二和周五下午 14:00-16:00 期间浏览量最高，建议在此时间段推送名片。',
      type: 'positive'
    },
    {
      icon: '🎯',
      title: '匹配优化建议',
      desc: '科技行业的匹配成功率比其他行业高 32%，建议增加科技行业标签以提高匹配效率。',
      type: 'suggestion'
    },
    {
      icon: '📊',
      title: '人脉增长趋势',
      desc: '本月新增人脉 23 位，环比增长 15%，人脉网络正在稳步扩展中。',
      type: 'positive'
    },
    {
      icon: '💡',
      title: '活跃度提升',
      desc: '您的个人资料完整度达到 85%，高于平台平均值，建议补充项目经历以提升完整度至 100%。',
      type: 'suggestion'
    }
  ]
}

Page({
  data: {
    // 原始统计数据（实际值）
    stats: { cardCount: 0, viewCount: 0, matchCount: 0 },
    // 动画显示的统计数据（从0递增到目标值）
    displayStats: { cardCount: 0, viewCount: 0, matchCount: 0 },
    // 趋势图数据
    chartData: [],
    // AI洞察建议
    insights: [],
    // 加载状态
    loading: true
  },

  onLoad() {
    const sys = wx.getSystemInfoSync()
    this.setData({ statusBarHeight: sys.statusBarHeight })
    wx.setNavigationBarTitle({ title: '数据洞察' })
    this.fetchData()
  },

  onPullDownRefresh() {
    this.fetchData()
  },

  // ==================== 数据获取 ====================

  fetchData() {
    this.setData({ loading: true })

    // 尝试请求 API — 按优先级依次尝试
    this._tryApi('/api/v1/analytics/dashboard')
      .then(resp => {
        this._handleApiResponse(resp)
      })
      .catch(() => {
        // 二级降级: 尝试 brochure/stats
        return this._tryApi('/api/v1/brochure/stats')
      })
      .then(resp => {
        if (resp) this._handleApiResponse(resp)
      })
      .catch(() => {
        // 最终降级: 使用模拟数据
        console.log('[Insight] 所有API不可达，使用模拟数据')
        this._applyData(FALLBACK_DATA)
      })
      .finally(() => {
        this.setData({ loading: false })
        wx.stopPullDownRefresh()
      })
  },

  /** 尝试调用一个API */
  _tryApi(url) {
    return new Promise((resolve, reject) => {
      get(url)
        .then(res => {
          // 兼容不同返回格式: res.data / res.code+res.data / 直接返回
          const data = res.data || res
          resolve(data)
        })
        .catch(err => {
          console.warn(`[Insight] API ${url} 不可用:`, err)
          reject(err)
        })
    })
  },

  /** 处理后端API响应，将其映射到前端数据结构 */
  _handleApiResponse(data) {
    // 尝试解析不同后端返回格式
    const stats = {
      cardCount: data.card_count ?? data.brochure_count ?? data.totalCards ?? data.stats?.cardCount ?? 0,
      viewCount: data.view_count ?? data.totalViews ?? data.stats?.viewCount ?? 0,
      matchCount: data.match_count ?? data.totalMatches ?? data.stats?.matchCount ?? 0
    }

    // 如果有chart_data或trend数据，转换
    let chartData = data.chart_data ?? data.trend ?? data.chartData
    if (chartData && Array.isArray(chartData) && chartData.length > 0) {
      chartData = chartData.map((item, i) => {
        const labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        const val = item.value ?? item.count ?? item.views ?? 0
        return {
          label: item.label || labels[i % 7],
          value: val,
          height: Math.max(20, Math.round(val / (stats.viewCount || 1) * 160))
        }
      })
    } else {
      // 生成默认7日趋势
      chartData = FALLBACK_DATA.chartData
    }

    // 如果有insights
    let insights = data.insights ?? data.suggestions ?? data.insightData
    if (!insights || !Array.isArray(insights) || insights.length === 0) {
      insights = FALLBACK_DATA.insights
    } else {
      insights = insights.map(item => ({
        icon: item.icon || '💡',
        title: item.title || item.name || '建议',
        desc: item.desc || item.description || item.content || '',
        type: item.type === 'suggestion' || item.type === 'warning' ? 'suggestion' : 'positive'
      }))
    }

    this._applyData({ stats, chartData, insights })
  },

  /** 将数据应用至页面，并启动滚动动画 */
  _applyData({ stats, chartData, insights }) {
    this.setData({
      stats,
      chartData,
      insights,
      displayStats: { cardCount: 0, viewCount: 0, matchCount: 0 }
    }, () => {
      // 数字滚动动画
      this._animateStats(stats)
    })
  },

  // ==================== 数字滚动动画 ====================

  _animateStats(target) {
    const duration = 800 // 动画持续ms
    const fps = 30
    const totalFrames = Math.round(duration / (1000 / fps))
    let frame = 0

    const step = {
      cardCount: target.cardCount / totalFrames,
      viewCount: target.viewCount / totalFrames,
      matchCount: target.matchCount / totalFrames
    }

    const timer = setInterval(() => {
      frame++
      if (frame >= totalFrames) {
        clearInterval(timer)
        this.setData({
          displayStats: {
            cardCount: target.cardCount,
            viewCount: target.viewCount,
            matchCount: target.matchCount
          }
        })
        return
      }
      this.setData({
        displayStats: {
          cardCount: Math.round(frame * step.cardCount),
          viewCount: Math.round(frame * step.viewCount),
          matchCount: Math.round(frame * step.matchCount)
        }
      })
    }, 1000 / fps)
  },

  // ==================== 导航 ====================

  goBack() {
    wx.navigateBack({
      delta: 1,
      fail: () => {
        wx.switchTab({ url: '/pages/index/index' })
      }
    })
  }
})
