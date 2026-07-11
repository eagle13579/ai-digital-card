/**
 * 模型服务管理 - 在线/离线状态监控
 * 支持 MockService 数据源 (useRealApi 开关)
 */
const MockService = require('../../../utils/mockService')

const MOCK_SERVICES = [
  {
    id: 'svc_llm',
    name: '大语言模型服务',
    model: 'DeepSeek-V4-Flash',
    status: 'online',
    uptime: '12天 7小时',
    latency: '320ms',
    requestsToday: 2847,
    gpuUtil: '67%',
    memoryUtil: '5.2GB / 16GB',
    version: 'v2.1.0',
  },
  {
    id: 'svc_embed',
    name: '文本向量化服务',
    model: 'text-embedding-v3',
    status: 'online',
    uptime: '12天 7小时',
    latency: '45ms',
    requestsToday: 15230,
    gpuUtil: '23%',
    memoryUtil: '1.8GB / 8GB',
    version: 'v1.8.3',
  },
  {
    id: 'svc_ocr',
    name: 'OCR识别服务',
    model: 'PaddleOCR-Edge',
    status: 'online',
    uptime: '8天 3小时',
    latency: '180ms',
    requestsToday: 892,
    gpuUtil: '41%',
    memoryUtil: '2.1GB / 8GB',
    version: 'v1.5.2',
  },
  {
    id: 'svc_reco',
    name: '推荐匹配服务',
    model: 'MatchNet-v2',
    status: 'degraded',
    uptime: '5天 12小时',
    latency: '890ms',
    requestsToday: 456,
    gpuUtil: '78%',
    memoryUtil: '3.6GB / 8GB',
    version: 'v2.0.1',
  },
  {
    id: 'svc_asr',
    name: '语音识别服务',
    model: 'Whisper-Large',
    status: 'offline',
    uptime: '0天',
    latency: '--',
    requestsToday: 0,
    gpuUtil: '0%',
    memoryUtil: '0GB / 4GB',
    version: 'v1.2.0',
  },
  {
    id: 'svc_img',
    name: '图像生成服务',
    model: 'StableDiffusion-XL',
    status: 'online',
    uptime: '3天 5小时',
    latency: '2.3s',
    requestsToday: 167,
    gpuUtil: '89%',
    memoryUtil: '11.2GB / 24GB',
    version: 'v1.9.5',
  },
]

Page({
  data: {
    useRealApi: false,
    loading: true,
    services: [],
    // 状态筛选
    filterStatus: 'all',
    stats: {
      total: 0,
      online: 0,
      degraded: 0,
      offline: 0,
    },
  },

  async onLoad() {
    await this.loadServices()
  },

  async loadServices() {
    this.setData({ loading: true })
    try {
      if (this.data.useRealApi) {
        // TODO: 对接真实模型服务管理API
        await new Promise(r => setTimeout(r, 800))
      } else {
        await new Promise(r => setTimeout(r, 600))
      }

      const services = MOCK_SERVICES
      const stats = { total: services.length, online: 0, degraded: 0, offline: 0 }
      services.forEach(s => { if (stats[s.status] !== undefined) stats[s.status]++ })

      this.setData({ services, stats, loading: false })
    } catch (e) {
      console.error('[ModelServe] 加载服务状态失败:', e)
      this.setData({ loading: false })
    }
  },

  filterByStatus(e) {
    const status = e.currentTarget.dataset.status
    this.setData({ filterStatus: status })
  },

  get filteredServices() {
    const { services, filterStatus } = this.data
    if (filterStatus === 'all') return services
    return services.filter(s => s.status === filterStatus)
  },

  refresh() {
    wx.showLoading({ title: '刷新中...' })
    this.loadServices().then(() => {
      wx.hideLoading()
      wx.showToast({ title: '已刷新', icon: 'success' })
    })
  },

  restartService(e) {
    const name = e.currentTarget.dataset.name
    wx.showModal({
      title: '重启服务',
      content: `确定要重启 "${name}" 吗？`,
      confirmText: '重启',
      confirmColor: '#ef4444',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '重启中...' })
          setTimeout(() => {
            wx.hideLoading()
            wx.showToast({ title: `${name} 已重启`, icon: 'success' })
          }, 2000)
        }
      },
    })
  },

  getStatusText(status) {
    const map = { online: '在线', degraded: '降级', offline: '离线' }
    return map[status] || status
  },

  getStatusColor(status) {
    const map = { online: '#22C55E', degraded: '#F59E0B', offline: '#EF4444' }
    return map[status] || '#9CA3AF'
  },

  onShareAppMessage() {
    return {
      title: '模型服务 - AI数智名片',
      path: '/pages/ai/modelserve',
    }
  },
})
