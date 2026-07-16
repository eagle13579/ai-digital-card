/**
 * 用户增长漏斗 Dashboard - 增长分析页面
 * 乘黄P9: 展示用户转化漏斗、留存数据和活跃用户统计
 */
const { analyticsApi } = require('../../../utils/api')
const i18n = require('../../../utils/i18n')

Page({
  data: {
    loading: true,
    // 时间范围: 7 或 30
    days: 30,
    // 关键指标
    dau: 0,
    wau: 0,
    mau: 0,
    totalReg: 0,
    // 增长漏斗
    funnel: [],
    // 留存率 [D0,D1,D3,D7,D14,D30]
    retention: [],
    // 事件分布
    events: [],
    // i18n
    _t: {},
  },

  onLoad() {
    this._loadI18n()
    this.loadData()
  },

  onShow() {
    this._loadI18n()
  },

  _loadI18n() {
    this.setData({ _t: i18n.getTranslations() })
  },

  async loadData() {
    this.setData({ loading: true })
    const days = this.data.days
    try {
      const [activeRes, funnelRes, retentionRes, eventRes] = await Promise.all([
        analyticsApi.getActiveUsers(days).catch(() => null),
        analyticsApi.getFunnel('activation').catch(() => null),
        analyticsApi.getRetention(days).catch(() => null),
        analyticsApi.getEventStats(days).catch(() => null),
      ])

      // 活跃用户
      const active = activeRes && activeRes.data ? activeRes.data : activeRes || {}
      this.setData({
        dau: active.dau || 0,
        wau: active.wau || 0,
        mau: active.mau || 0,
        totalReg: active.total_registrations || active.totalRegistrations || 0,
      })

      // 漏斗数据 — 映射5步
      const rawFunnel = funnelRes && funnelRes.data ? funnelRes.data : funnelRes || []
      const funnelSteps = [
        { key: 'register',        labelKey: 'funnelStep1' },
        { key: 'create_card',     labelKey: 'funnelStep2' },
        { key: 'view_recommend',  labelKey: 'funnelStep3' },
        { key: 'send_connect',    labelKey: 'funnelStep4' },
        { key: 'paid_member',     labelKey: 'funnelStep5' },
      ]
      const formattedFunnel = funnelSteps.map((step, idx) => {
        const raw = rawFunnel[idx] || {}
        return {
          label: this.data._t[step.labelKey] || step.labelKey,
          users: raw.user_count || raw.users || 0,
          rate: this._fmtRate(raw.conversion_rate),
          dropoff: this._fmtRate(raw.dropoff_rate),
        }
      })
      this.setData({ funnel: formattedFunnel })

      // 留存数据
      const rawRetention = retentionRes && retentionRes.data ? retentionRes.data : retentionRes || []
      const retentionLabels = ['D0', 'D1', 'D3', 'D7', 'D14', 'D30']
      const formattedRetention = retentionLabels.map((label, idx) => {
        const raw = rawRetention[idx] || {}
        return {
          label,
          rate: this._fmtRate(raw.rate || raw.retention_rate),
        }
      })
      this.setData({ retention: formattedRetention })

      // 事件分布
      const rawEvents = eventRes && eventRes.data ? eventRes.data : eventRes || []
      const formattedEvents = Array.isArray(rawEvents)
        ? rawEvents.map(e => ({
            name: e.event_name || e.name || e.event_type || '-',
            count: e.count || e.event_count || 0,
            percentage: this._fmtRate(e.percentage || e.ratio),
          }))
        : []
      this.setData({ events: formattedEvents })
    } catch (err) {
      console.error('[Growth] 加载增长数据失败:', err)
    } finally {
      this.setData({ loading: false })
    }
  },

  /** 切换时间范围 */
  switchTimeRange(e) {
    const days = parseInt(e.currentTarget.dataset.days, 10)
    if (days === this.data.days) return
    this.setData({ days }, () => this.loadData())
  },

  /** 格式化百分比: 保留1位小数 */
  _fmtRate(val) {
    if (val === undefined || val === null) return '0.0'
    const num = typeof val === 'string' ? parseFloat(val) : val
    if (isNaN(num)) return '0.0'
    return (num * 100).toFixed(1)
  },
})
