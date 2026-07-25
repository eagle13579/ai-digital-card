/**
 * progressive_search/index.js — 渐进式人脉搜索页面逻辑
 *
 * 两阶段搜索:
 *   Phase 1 (广度撒网): 标签/关键词匹配
 *   Phase 2 (深度挖掘): 多层关系扩展
 */

const app = getApp();

Page({
  data: {
    query: '',
    searching: false,
    result: null,
    error: null,

    // 配置
    configExpanded: false,
    modeOptions: ['hybrid (混合)', 'score (评分)', 'count (数量)'],
    modeIndex: 0,
    maxWide: 20,
    depth: 3,
    minScoreTimes10: 3,

    // 预计算视图变量（避免WXML中出现.属性访问和方法调用）
    showEmptyState: true,
    showResults: false,
    showTransitionBanner: false,
    showTransitionDivider: false,
    hasError: false,
    errorMessage: '',
    phase1List: [],
    phase1Count: '',
    phase1Empty: false,
    phase2List: [],
    phase2Count: '',
    phase2NotEmpty: false,
    transitionBannerClass: 'waiting',
    transitionBannerText: '',
    transitionDetailText: '',
    transitionDividerText: '',
    searchStatsText: '',
    searchIdText: '',
    phase2IndicatorClass: 'dim',
  },

  onLoad(options) {
    if (options.q) {
      this.setData({ query: options.q });
      this.onSearch();
    }
  },

  onPullDownRefresh() {
    if (this.data.query) {
      this.onSearch().then(() => wx.stopPullDownRefresh());
    } else {
      wx.stopPullDownRefresh();
    }
  },

  async onSearch() {
    const { query, maxWide, depth, modeIndex, minScoreTimes10 } = this.data;
    const q = query.trim();

    if (!q) {
      wx.showToast({ title: '请输入搜索关键词', icon: 'none' });
      return;
    }

    this.setData({
      searching: true,
      hasError: false,
      errorMessage: '',
      showEmptyState: false,
      showResults: false,
    });

    try {
      const params = new URLSearchParams();
      params.set('q', q);
      params.set('max_wide', String(maxWide));
      params.set('depth', String(depth));
      params.set('min_score', String(minScoreTimes10 / 10));
      params.set('mode', this._getModeValue(modeIndex));

      const url = `${this.data.apiBase || '/api'}/search/progressive?${params.toString()}`;

      const res = await new Promise((resolve, reject) => {
        wx.request({
          url,
          method: 'GET',
          success: (resp) => resolve(resp.data),
          fail: (err) => reject(err),
        });
      });

      if (res.code !== 0) {
        throw new Error(res.message || '搜索失败 (' + res.code + ')');
      }

      this._updateView(res.data);

    } catch (err) {
      console.error('[ProgressiveSearch] 搜索失败:', err);
      this.setData({
        searching: false,
        hasError: true,
        errorMessage: err.message || '搜索请求失败',
      });
    }
  },

  _updateView(data) {
    // 预处理列表项
    const phase1List = (data.phase1_wide || []).map(item => this._processItem(item));
    const phase2List = (data.phase2_deep || []).map(item => this._processItem(item));

    const trans = data.transition || null;

    this.setData({
      result: data,
      searching: false,
      showResults: true,
      showEmptyState: false,

      // Phase 1
      phase1List: phase1List,
      phase1Count: phase1List.length + ' 条结果',
      phase1Empty: phase1List.length === 0,

      // Phase 2
      phase2List: phase2List,
      phase2Count: phase2List.length + ' 条结果',
      phase2NotEmpty: phase2List.length > 0,

      // 过渡横幅
      showTransitionBanner: trans !== null,
      transitionBannerClass: trans && trans.should_deep ? 'ready' : 'waiting',
      transitionBannerText: trans && trans.should_deep ? '🚀 进入深度挖掘' : '⏳ 广度撒网中',

      showTransitionDivider: trans !== null,
      transitionDividerText: trans && trans.should_deep ? '⬇️ 过渡至深度挖掘' : '🤔 条件未满足',
      transitionDetailText: trans
        ? '模式: ' + trans.transition_mode + ' | 结果: ' + trans.total_wide + '条 | 最高分: ' + (trans.max_score || 0)
        : '',

      // 统计
      searchStatsText: '搜索耗时: ' + (data.elapsed_ms || 0) + 'ms | 共 ' + (data.total_found || 0) + ' 条结果',
      searchIdText: 'ID: ' + (data.search_id || ''),

      // 加载状态
      phase2IndicatorClass: trans && trans.should_deep ? 'deep-active' : 'dim',
    });
  },

  _processItem(item) {
    if (!item) return item;
    item.scoreClass = item.match_score >= 0.7 ? 'high' : item.match_score >= 0.4 ? 'mid' : 'low';
    item.scoreDisplay = (item.match_score * 100).toFixed(0);
    item.hasTrustScore = item.trust_score !== undefined;
    item.trustScoreDisplay = item.hasTrustScore ? (item.trust_score * 100).toFixed(0) : '0';
    item.viaName = item.via || '';
    item.title = item.title || '未知职位';
    item.company = item.company || '';
    return item;
  },

  _getModeValue(index) {
    return ['hybrid', 'score', 'count'][index] || 'hybrid';
  },

  onQueryInput(e) {
    this.setData({ query: e.detail.value });
  },

  toggleConfig() {
    this.setData({ configExpanded: !this.data.configExpanded });
  },

  onModeChange(e) {
    this.setData({ modeIndex: e.detail.value });
  },

  onMaxWideChange(e) {
    this.setData({ maxWide: e.detail.value });
  },

  onDepthChange(e) {
    this.setData({ depth: e.detail.value });
  },

  onMinScoreChange(e) {
    this.setData({ minScoreTimes10: e.detail.value });
  },

  onShareAppMessage() {
    const q = this.data.query;
    return {
      title: q ? '渐进式人脉搜索: ' + q : '渐进式人脉搜索',
      path: '/pages/progressive_search/index' + (q ? '?q=' + encodeURIComponent(q) : ''),
    };
  },
});
