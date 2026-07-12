/**
 * AI匹配推荐 - 智能匹配筛选
 */
const MockService = require('../../../utils/mockService')

Page({
  data: {
    matches: [],
    filteredMatches: [],
    industries: ['全部', '科技', '金融', '制造', '教育', '医疗'],
    regions: ['全部', '北京', '上海', '深圳', '杭州', '广州'],
    selectedIndustry: '全部',
    selectedRegion: '全部',
    selectedIndustryIndex: 0,
    selectedRegionIndex: 0,
    loading: false,

    // 解锁详情
    showDetail: false,
    unlockedItem: null,
    exchangeDone: false,
  },

  async onLoad() {
    this.setData({ loading: true })
    try {
      const matches = await MockService.getRecommendList()
      this.setData({ matches, filteredMatches: matches, loading: false })
    } catch (e) {
      console.error('获取匹配列表失败', e)
      this.setData({ loading: false })
    }
  },

  onIndustryChange(e) {
    const val = this.data.industries[e.detail.value]
    this.setData({ selectedIndustry: val })
    this.applyFilters()
  },

  onRegionChange(e) {
    const val = this.data.regions[e.detail.value]
    this.setData({ selectedRegion: val })
    this.applyFilters()
  },

  applyFilters() {
    const { matches, selectedIndustry, selectedRegion } = this.data
    let filtered = [...matches]

    if (selectedIndustry !== '全部') {
      filtered = filtered.filter(m => m.industry && m.industry.includes(selectedIndustry))
    }
    if (selectedRegion !== '全部') {
      filtered = filtered.filter(m => m.region && m.region.includes(selectedRegion))
    }

    this.setData({ filteredMatches: filtered })
  },

  unlock(e) {
    const id = e.currentTarget.dataset.id
    const item = this.data.filteredMatches.find(m => m.id === id)
    if (!item) {
      wx.showToast({ title: '未找到匹配用户', icon: 'none' })
      return
    }
    this.setData({
      unlockedItem: item,
      showDetail: true,
      exchangeDone: false,
    })
  },

  backToList() {
    this.setData({
      showDetail: false,
      unlockedItem: null,
      exchangeDone: false,
    })
  },

  exchangeCard() {
    this.setData({ exchangeDone: true })
    wx.showToast({ title: '✓ 已发送名片交换请求', icon: 'success' })
  },
})
