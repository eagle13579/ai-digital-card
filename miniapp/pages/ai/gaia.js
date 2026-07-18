// STUB: 后端AI模块未就绪，页面使用Mock数据
/**
 * 盖娅进化大脑 - AI进化仪表盘
 * 展示知识图谱状态、进化指标、Agent状态
 * 支持 MockService 数据源 (useRealApi 开关)
 */
const { MockService } = require('../../../utils/mockService')

const MOCK_GAIA_DATA = {
  status: 'active',
  brainName: '盖娅·α',
  evolutionLevel: 3,
  metrics: [
    { id: 'nodes', label: '知识节点', value: 128, icon: '🧠', trend: 'up' },
    { id: 'connections', label: '连接数', value: 1024, icon: '🔗', trend: 'up' },
    { id: 'evolution', label: '进化值', value: 86, icon: '⚡', trend: 'up' },
    { id: 'memory', label: '记忆容量', value: '2.4TB', icon: '💾', trend: 'stable' },
  ],
  dataFlow: { inbound: 256, outbound: 189, processed: 445 },
  agents: [
    { id: 'a1', name: 'Hermes', emoji: '🔮', role: '推理引擎', status: 'online' },
    { id: 'a2', name: 'Athena', emoji: '🦉', role: '知识提取', status: 'online' },
    { id: 'a3', name: 'Prometheus', emoji: '🔥', role: '内容生成', status: 'online' },
    { id: 'a4', name: 'Iris', emoji: '🌈', role: '数据感知', status: 'idle' },
  ],
  knowledge: [
    { id: 'k1', title: '深度学习架构演进', desc: 'Transformer → MoE → Mamba架构对比分析', source: '论文摘要', confidence: '92%', type: 'tech' },
    { id: 'k2', title: '用户画像聚类分析', desc: '基于RFM模型的B2B用户分层策略', source: '数据分析', confidence: '87%', type: 'insight' },
    { id: 'k3', title: '行业知识图谱构建', desc: '从名片数据自动提取实体关系三元组', source: '系统学习', confidence: '95%', type: 'knowledge' },
  ],
}

// Mock gaia_router API call
async function mockGaiaRouter(action, params) {
  await new Promise(r => setTimeout(r, 600 + Math.random() * 600))
  return { success: true, data: MOCK_GAIA_DATA }
}

Page({
  data: {
    useRealApi: false,
    loading: true,
    gaiaData: null,
    error: null,
    // 学习模式
    learningMode: false,
  },

  async onLoad() {
    await this.loadGaiaData()
  },

  async loadGaiaData() {
    this.setData({ loading: true, error: null })
    try {
      if (this.data.useRealApi) {
        // 连接后端 gaia_router
        const res = await mockGaiaRouter('getDashboard')
        this.setData({ gaiaData: res.data, loading: false })
      } else {
        await new Promise(r => setTimeout(r, 800))
        this.setData({ gaiaData: MOCK_GAIA_DATA, loading: false })
      }
    } catch (e) {
      console.error('[Gaia] 加载失败:', e)
      this.setData({ loading: false, error: '加载盖娅数据失败，请稍后重试' })
    }
  },

  refresh() {
    wx.showLoading({ title: '刷新中...' })
    this.loadGaiaData().then(() => {
      wx.hideLoading()
      wx.showToast({ title: '已更新', icon: 'success' })
    })
  },

  toggleLearn() {
    this.setData({ learningMode: !this.data.learningMode })
    if (this.data.learningMode) {
      wx.showToast({ title: '进入学习模式', icon: 'none' })
    }
  },

  viewKnowledge(e) {
    const id = e.currentTarget.dataset.id
    wx.showToast({ title: `查看知识: ${id}`, icon: 'none' })
  },

  viewAllKnowledge() {
    wx.showToast({ title: '所有知识节点', icon: 'none' })
  },

  viewAgent(e) {
    const name = e.currentTarget.dataset.name
    wx.showToast({ title: `${name} 详情`, icon: 'none' })
  },

  triggerEvolution() {
    wx.showLoading({ title: '进化中...' })
    setTimeout(() => {
      wx.hideLoading()
      wx.showModal({
        title: '🧬 进化完成',
        content: '盖娅大脑进化至 Lv.4，新增「协同推理」能力',
        showCancel: false,
      })
    }, 2000)
  },

  onShareAppMessage() {
    return {
      title: '盖娅进化大脑 - AI数智名片',
      path: '/pages/ai/gaia',
    }
  },
})
