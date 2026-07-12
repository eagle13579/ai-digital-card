/**
 * A/B测试管理 - 实验方案列表与状态
 * 支持 MockService 数据源 (useRealApi 开关)
 */
const { MockService } = require('../../../utils/mockService')

const MOCK_EXPERIMENTS = [
  {
    id: 'exp_001',
    name: '名片模板样式测试',
    description: '对比新版磨砂玻璃风格 vs 经典卡片风格转化率',
    status: 'running',
    startedAt: '2026-07-01',
    variants: [
      { name: 'A: 经典', traffic: 50, conversion: 3.2, users: 1240 },
      { name: 'B: 磨砂玻璃', traffic: 50, conversion: 4.7, users: 1180 },
    ],
    winner: null,
    duration: '7天',
  },
  {
    id: 'exp_002',
    name: 'AI对话欢迎语测试',
    description: '测试不同欢迎语对用户互动率的影响',
    status: 'running',
    startedAt: '2026-07-08',
    variants: [
      { name: 'A: 简洁版', traffic: 50, conversion: 18.5, users: 560 },
      { name: 'B: 详细版', traffic: 50, conversion: 22.1, users: 540 },
    ],
    winner: null,
    duration: '5天',
  },
  {
    id: 'exp_003',
    name: '首页推荐算法',
    description: '协同过滤 vs 基于内容的推荐效果对比',
    status: 'paused',
    startedAt: '2026-06-20',
    variants: [
      { name: 'A: 协同过滤', traffic: 50, conversion: 6.8, users: 3200 },
      { name: 'B: 内容推荐', traffic: 50, conversion: 7.2, users: 3150 },
    ],
    winner: null,
    duration: '暂停',
  },
  {
    id: 'exp_004',
    name: '扫码支付引导优化',
    description: '支付页面不同引导文案的转化效果',
    status: 'completed',
    startedAt: '2026-06-10',
    variants: [
      { name: 'A: 原版', traffic: 50, conversion: 12.3, users: 890 },
      { name: 'B: 优化版', traffic: 50, conversion: 18.6, users: 870 },
    ],
    winner: 'B',
    duration: '已结束',
  },
  {
    id: 'exp_005',
    name: '推送文案A/B测试',
    description: '测试不同推送文案的消息点击率',
    status: 'draft',
    variants: [
      { name: 'A: 功能导向', traffic: 50, conversion: 0, users: 0 },
      { name: 'B: 利益导向', traffic: 50, conversion: 0, users: 0 },
    ],
    winner: null,
    duration: '未开始',
  },
]

Page({
  data: {
    useRealApi: false,
    loading: true,
    experiments: [],
    filterStatus: 'all', // all | running | paused | completed | draft
    statusLabels: {
      running: '运行中',
      paused: '已暂停',
      completed: '已完成',
      draft: '草稿',
    },
    statusColors: {
      running: '#22C55E',
      paused: '#F59E0B',
      completed: '#0EA5E9',
      draft: '#9CA3AF',
    },
  },

  async onLoad() {
    await this.loadExperiments()
  },

  async loadExperiments() {
    this.setData({ loading: true })
    try {
      if (this.data.useRealApi) {
        // TODO: 对接真实API
        await new Promise(r => setTimeout(r, 600))
        this.setData({ experiments: MOCK_EXPERIMENTS, loading: false })
      } else {
        await new Promise(r => setTimeout(r, 500))
        this.setData({ experiments: MOCK_EXPERIMENTS, loading: false })
      }
    } catch (e) {
      console.error('[ABTest] 加载失败:', e)
      this.setData({ loading: false })
    }
  },

  filterByStatus(e) {
    const status = e.currentTarget.dataset.status
    this.setData({ filterStatus: status })
  },

  get filteredExperiments() {
    const { experiments, filterStatus } = this.data
    if (filterStatus === 'all') return experiments
    return experiments.filter(e => e.status === filterStatus)
  },

  createExperiment() {
    wx.showToast({ title: '创建实验 (开发中)', icon: 'none' })
  },

  viewDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.showToast({ title: `查看实验: ${id}`, icon: 'none' })
  },

  onShareAppMessage() {
    return {
      title: 'A/B测试 - AI数智名片',
      path: '/pages/ai/abtest',
    }
  },
})
