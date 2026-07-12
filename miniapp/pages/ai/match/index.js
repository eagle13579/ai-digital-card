/**
 * AI匹配推荐 - 智能匹配筛选 (i18n enabled)
 * P2-10: 匹配推荐池扩充 — 支持翻页/加载更多
 */
const { MockService } = require('../../../utils/mockService')
const { matchApi, connectionApi } = require('../../../utils/api')
const i18n = require('../../../utils/i18n')

const PAGE_SIZE = 10 // 每页10条

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
    // 翻页
    page: 1,
    hasMore: true,
    loadingMore: false,

    // 解锁详情
    showDetail: false,
    unlockedItem: null,
    exchangeDone: false,

    // i18n
    _t: {},
  },

  onLoad() {
    this._loadI18n()
    this.loadRecommend()
  },

  onShow() {
    this._loadI18n()
  },

  /** 加载国际化翻译 */
  _loadI18n() {
    this.setData({
      _t: i18n.getTranslations(),
      industries: i18n.tArray('industries'),
      regions: i18n.tArray('regions'),
    })
    // 重置选中索引，确保显示的文本正确
    this.setData({
      selectedIndustry: this.data.industries[this.data.selectedIndustryIndex] || this.data.industries[0],
      selectedRegion: this.data.regions[this.data.selectedRegionIndex] || this.data.regions[0],
    })
  },

  /** 加载推荐列表 */
  async loadRecommend() {
    this.setData({ loading: true, page: 1, hasMore: true })
    try {
      if (MockService.USE_MOCK) {
        const res = await MockService.getRecommendList(1, PAGE_SIZE)
        const list = res.data || res
        this.setData({
          matches: list,
          filteredMatches: list,
          loading: false,
          hasMore: list.length >= PAGE_SIZE,
        })
      } else {
        const res = await matchApi.getRecommendList(1, PAGE_SIZE)
        const list = res.data || res || []
        this.setData({
          matches: list,
          filteredMatches: list,
          loading: false,
          hasMore: list.length >= PAGE_SIZE,
        })
      }
    } catch (e) {
      console.error('获取匹配列表失败', e)
      this.setData({ loading: false })
    }
  },

  /** 加载更多（翻页） */
  async loadMore() {
    if (this.data.loadingMore || !this.data.hasMore) return
    this.setData({ loadingMore: true })
    const nextPage = this.data.page + 1
    try {
      let newItems = []
      if (MockService.USE_MOCK) {
        const res = await MockService.getRecommendList(nextPage, PAGE_SIZE)
        newItems = res.data || res || []
      } else {
        const res = await matchApi.getRecommendList(nextPage, PAGE_SIZE)
        newItems = res.data || res || []
      }
      const merged = [...this.data.matches, ...newItems]
      this.setData({
        matches: merged,
        filteredMatches: merged,
        page: nextPage,
        hasMore: newItems.length >= PAGE_SIZE,
        loadingMore: false,
      })
    } catch (e) {
      console.error('加载更多匹配失败', e)
      this.setData({ loadingMore: false })
    }
  },

  onIndustryChange(e) {
    const val = this.data.industries[e.detail.value]
    this.setData({ selectedIndustry: val, selectedIndustryIndex: e.detail.value })
    this.applyFilters()
  },

  onRegionChange(e) {
    const val = this.data.regions[e.detail.value]
    this.setData({ selectedRegion: val, selectedRegionIndex: e.detail.value })
    this.applyFilters()
  },

  applyFilters() {
    const { matches, selectedIndustry, selectedRegion } = this.data
    let filtered = [...matches]

    const all = i18n.t('all')
    if (selectedIndustry !== all) {
      filtered = filtered.filter(m => m.industry && m.industry.includes(selectedIndustry))
    }
    if (selectedRegion !== all) {
      filtered = filtered.filter(m => m.region && m.region.includes(selectedRegion))
    }

    this.setData({ filteredMatches: filtered })
  },

  unlock(e) {
    const id = e.currentTarget.dataset.id
    const item = this.data.filteredMatches.find(m => m.id === id)
    if (!item) {
      wx.showToast({ title: i18n.t('notFoundUser'), icon: 'none' })
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

  async exchangeCard() {
    if (!this.data.unlockedItem) return
    try {
      await connectionApi.request(this.data.unlockedItem.id, '', 'match')
      this.setData({ exchangeDone: true })
      wx.showToast({ title: i18n.t('requestSent'), icon: 'success' })
    } catch (e) {
      console.error('交换名片失败', e)
    }
  },
})
