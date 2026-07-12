/**
 * 搜索页面 - 发现用户
 * 支持关键词搜索 + 行业/地区筛选 + 分页
 */
const { userApi, tagApi } = require('../../utils/api')

// 防抖延时
const DEBOUNCE_MS = 300

Page({
  data: {
    keyword: '',
    industryIndex: 0,
    regionIndex: 0,
    industryList: ['不限'],
    regionList: ['不限'],
    results: [],
    page: 1,
    pageSize: 20,
    hasMore: false,
    loading: false,
    loadingMore: false,
    hasSearched: false,
    defaultAvatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20person%20portrait%20headshot%20clean%20white%20background&image_size=square',
  },

  onLoad() {
    this._loadFilterOptions()
  },

  /** 加载筛选选项（行业标签+地区标签） */
  async _loadFilterOptions() {
    try {
      // 从标签列表获取行业和地区选项
      const tags = await tagApi.list().catch(() => [])
      const tagList = Array.isArray(tags) ? tags : (tags.data || tags || [])
      const industries = ['不限']
      const regions = ['不限']
      if (Array.isArray(tagList)) {
        tagList.forEach(t => {
          if (t.tag_type === 'provide' && t.tag && !industries.includes(t.tag)) {
            industries.push(t.tag)
          }
          if (t.tag_type === 'need' && t.tag && !regions.includes(t.tag)) {
            regions.push(t.tag)
          }
        })
      }
      this.setData({ industryList: industries, regionList: regions })
    } catch (err) {
      console.warn('[Search] 加载筛选选项失败:', err)
    }
  },

  /** 关键词输入（防抖 300ms） */
  onKeywordInput(e) {
    const keyword = e.detail.value
    this.setData({ keyword })
    if (this._debounceTimer) clearTimeout(this._debounceTimer)
    this._debounceTimer = setTimeout(() => {
      this._doSearch()
    }, DEBOUNCE_MS)
  },

  /** 清除关键词 */
  clearKeyword() {
    this.setData({ keyword: '', results: [], page: 1, hasMore: false, hasSearched: false })
    if (this._debounceTimer) clearTimeout(this._debounceTimer)
  },

  /** 行业筛选变化 */
  onIndustryChange(e) {
    this.setData({ industryIndex: e.detail.value })
  },

  /** 地区筛选变化 */
  onRegionChange(e) {
    this.setData({ regionIndex: e.detail.value })
  },

  /** 点击搜索按钮 */
  onSearch() {
    this._doSearch()
  },

  /** 执行搜索 */
  async _doSearch() {
    const { keyword, industryIndex, regionIndex, industryList, regionList } = this.data

    this.setData({ loading: true, page: 1, hasSearched: true })

    try {
      const params = { q: keyword, page: 1, page_size: this.data.pageSize }
      if (industryIndex > 0) params.industry = industryList[industryIndex]
      if (regionIndex > 0) params.region = regionList[regionIndex]

      const res = await userApi.search(params)
      // 支持 { items, total, page, has_more } 和 { data: { items, ... } } 格式
      const data = res && res.items ? res : (res?.data || res || {})
      const items = data.items || []
      const hasMore = data.has_more || false

      this.setData({
        results: items,
        hasMore,
        loading: false,
        loadingMore: false,
      })
    } catch (err) {
      console.error('[Search] 搜索失败:', err)
      this.setData({ loading: false, loadingMore: false })
    }
  },

  /** 加载更多 */
  async onLoadMore() {
    if (this.data.loadingMore || !this.data.hasMore || this.data.loading) return

    this.setData({ loadingMore: true })
    const nextPage = this.data.page + 1

    try {
      const { keyword, industryIndex, regionIndex, industryList, regionList } = this.data
      const params = { q: keyword, page: nextPage, page_size: this.data.pageSize }
      if (industryIndex > 0) params.industry = industryList[industryIndex]
      if (regionIndex > 0) params.region = regionList[regionIndex]

      const res = await userApi.search(params)
      const data = res && res.items ? res : (res?.data || res || {})
      const items = data.items || []
      const hasMore = data.has_more || false

      this.setData({
        results: [...this.data.results, ...items],
        page: nextPage,
        hasMore,
        loadingMore: false,
      })
    } catch (err) {
      console.error('[Search] 加载更多失败:', err)
      this.setData({ loadingMore: false })
    }
  },

  /** 跳转用户详情 */
  goUserDetail(e) {
    const user = e.currentTarget.dataset.user
    if (user && user.id) {
      wx.navigateTo({ url: `/pages/card/card?id=${user.id}` })
    }
  },
})