/**
 * AI匹配推荐 - 智能匹配筛选 (i18n enabled)
 * P2-10: 匹配推荐池扩充 — 支持翻页/加载更多
 */
const { getRecommend } = require('../../../utils/ai-bridge')
const { connectionApi, transpheeApi } = require('../../../utils/api')
const i18n = require('../../../utils/i18n')
const cache = require('../../../utils/cache')

const PAGE_SIZE = 10 // 每页10条
const MATCH_CACHE_KEY = 'match:recommend' // 推荐列表缓存键
const MATCH_CACHE_TTL = 30 * 60 * 1000 // 30分钟过期

Page({
  data: {
    // 模式: people=人脉匹配(标签引擎) | company=企业匹配(三蛋蛋1000万企业库)
    mode: 'people',
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
    useRealApi: true,

    // 解锁详情
    showDetail: false,
    unlockedItem: null,
    exchangeDone: false,

    // ── 企业匹配 (Transphee) ──
    companyName: '',
    product: '',
    business: '',
    typicalCustomers: '',
    companyMatches: [],
    companyPage: 1,
    companyHasMore: false,
    companyLoading: false,
    companyTotal: 0,
    companyTotalLowerBound: false,
    companyQuota: null,

    // i18n
    _t: {},
  },

  onLoad() {
    this._loadI18n()
    // 登录守卫
    const store = require('../../../utils/store')
    if (!store.getState().isLoggedIn) {
      wx.redirectTo({ url: '/pages/login/index' })
      return
    }
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

  /** 加载推荐列表（缓存优先策略） */
  async loadRecommend() {
    this.setData({ loading: true, page: 1, hasMore: true })
    try {
      // 使用 cacheFirst 策略：先返回缓存，后台静默刷新
      const list = await cache.cacheFirst(MATCH_CACHE_KEY, async () => {
        const res = await getRecommend({ page: 1, pageSize: PAGE_SIZE }, this.data.useRealApi)
        const items = res.data || res || []
        return items
      }, { ttl: MATCH_CACHE_TTL })

      this.setData({
        matches: list,
        filteredMatches: list,
        loading: false,
        hasMore: list.length >= PAGE_SIZE,
      })
    } catch (e) {
      console.error('获取匹配列表失败', e)
      this.setData({ loading: false })
      // 尝试从独立缓存键读取（兜底）
      const fallback = cache.get('match:list_v1', { ignoreExpiry: true })
      if (fallback && fallback.length > 0) {
        console.log('[Match] 兜底缓存命中')
        this.setData({ matches: fallback, filteredMatches: fallback, loading: false })
      }
    }
  },

  /** 加载更多（翻页 + 网络优先策略） */
  async loadMore() {
    if (this.data.loadingMore || !this.data.hasMore) return
    this.setData({ loadingMore: true })
    const nextPage = this.data.page + 1
    try {
      const cacheKey = `${MATCH_CACHE_KEY}:page:${nextPage}`
      const newItems = await cache.networkFirst(cacheKey, async () => {
        const res = await getRecommend({ page: nextPage, pageSize: PAGE_SIZE }, this.data.useRealApi)
        return res.data || res || []
      }, { ttl: MATCH_CACHE_TTL })

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

  /** 从列表直接发起交换名片（无需解锁） */
  async exchangeFromList(e) {
    const id = e.currentTarget.dataset.id
    const item = this.data.filteredMatches.find(m => m.id === id)
    if (!item) return
    try {
      await connectionApi.request(id, '', 'match')
      // 标记该卡片已发送请求
      const matches = [...this.data.matches]
      const idx = matches.findIndex(m => m.id === id)
      if (idx > -1) {
        matches[idx] = { ...matches[idx], _requestSent: true }
      }
      const filtered = [...this.data.filteredMatches]
      const fidx = filtered.findIndex(m => m.id === id)
      if (fidx > -1) {
        filtered[fidx] = { ...filtered[fidx], _requestSent: true }
      }
      this.setData({ matches, filteredMatches: filtered })
      wx.showToast({ title: i18n.t('requestSent'), icon: 'success' })
    } catch (e) {
      console.error('直接交换名片失败', e)
    }
  },

  // ═══════════════ 企业匹配 (三蛋蛋 1000万企业库) ═══════════════

  /** 切换模式: people | company */
  switchMode(e) {
    const mode = e.currentTarget.dataset.mode
    if (mode === this.data.mode) return
    this.setData({ mode })
    if (mode === 'company' && this.data.companyQuota === null) {
      this.loadCompanyQuota()
    }
  },

  /** 表单输入 */
  onCompanyNameInput(e) {
    this.setData({ companyName: e.detail.value })
  },
  onProductInput(e) {
    this.setData({ product: e.detail.value })
  },
  onBusinessInput(e) {
    this.setData({ business: e.detail.value })
  },
  onTypicalCustomersInput(e) {
    this.setData({ typicalCustomers: e.detail.value })
  },

  /** 今日配额 */
  async loadCompanyQuota() {
    try {
      const res = await transpheeApi.quota()
      this.setData({ companyQuota: res && res.data ? res.data : res })
    } catch (e) {
      console.error('获取企业匹配配额失败', e)
    }
  },

  /**
   * 企业匹配查询: 输入卖家信息 → 潜在买家名单
   * company_name 必填; product/business/typical_customers 至少填一
   */
  async searchCompanyMatch() {
    const { companyName, product, business, typicalCustomers } = this.data
    if (!companyName) {
      wx.showToast({ title: i18n.t('companyNameRequired'), icon: 'none' })
      return
    }
    if (!product && !business && !typicalCustomers) {
      wx.showToast({ title: i18n.t('companyMatchParamRequired'), icon: 'none' })
      return
    }
    this.setData({ companyLoading: true })
    try {
      const res = await transpheeApi.match({
        company_name: companyName,
        product,
        business,
        typical_customers: typicalCustomers,
        page: 1,
      })
      const d = (res && res.data) ? res.data : (res || {})
      const list = d.list || []
      this.setData({
        companyMatches: list,
        companyPage: 1,
        companyHasMore: list.length >= 20,
        companyLoading: false,
        companyTotal: d.total || 0,
        companyTotalLowerBound: !!d.total_is_lower_bound,
        companyQuota: res && res.quota ? res.quota : this.data.companyQuota,
      })
    } catch (e) {
      console.error('企业匹配失败', e)
      this.setData({ companyLoading: false })
      const msg = (e && e.message) ? e.message : i18n.t('companyMatchFailed')
      wx.showToast({ title: msg, icon: 'none' })
    }
  },

  /** 企业匹配翻页 (page>=2 恒20条) */
  async loadCompanyMore() {
    if (this.data.companyLoading || !this.data.companyHasMore) return
    this.setData({ companyLoading: true })
    const nextPage = this.data.companyPage + 1
    try {
      const res = await transpheeApi.match({
        company_name: this.data.companyName,
        product: this.data.product,
        business: this.data.business,
        typical_customers: this.data.typicalCustomers,
        page: nextPage,
      })
      const d = (res && res.data) ? res.data : (res || {})
      const list = d.list || []
      // 跨页去重按 cname (三蛋蛋规范)
      const seen = new Set(this.data.companyMatches.map(m => m.cname))
      const fresh = list.filter(m => !seen.has(m.cname))
      this.setData({
        companyMatches: [...this.data.companyMatches, ...fresh],
        companyPage: nextPage,
        companyHasMore: list.length >= 20,
        companyLoading: false,
        companyTotal: d.total || this.data.companyTotal,
        companyTotalLowerBound: !!d.total_is_lower_bound,
      })
    } catch (e) {
      console.error('企业匹配翻页失败', e)
      this.setData({ companyLoading: false })
      wx.showToast({ title: i18n.t('companyMatchFailed'), icon: 'none' })
    }
  },
})
