/**
 * progressive_search/index.js — 渐进式人脉搜索页面逻辑
 *
 * 两阶段搜索:
 *   Phase 1 (广度撒网): 标签/关键词匹配
 *   Phase 2 (深度挖掘): 多层关系扩展
 *
 * API 路径: GET /api/search/progressive
 *   参数: q, depth, max_wide, min_score, mode
 */

const app = getApp();

Page({
  data: {
    // 搜索
    query: '',
    searching: false,
    result: null,
    error: null,
    transitionReady: false,
    transitionInfo: null,

    // 配置
    configExpanded: false,
    modeOptions: ['hybrid (混合)', 'score (评分)', 'count (数量)'],
    modeIndex: 0,
    maxWide: 20,
    depth: 3,
    minScore: 3,  // 0.3 * 10

    // 后端 API 基础路径
    apiBase: app.globalData?.apiBase || '/api',
  },

  /* ── 生命周期 ─────────────────────────── */

  onLoad(options) {
    // 如果从外部传入搜索参数
    if (options.q) {
      this.setData({ query: options.q });
      this.onSearch();
    }
  },

  onPullDownRefresh() {
    if (this.data.query) {
      this.onSearch().then(() => {
        wx.stopPullDownRefresh();
      });
    } else {
      wx.stopPullDownRefresh();
    }
  },

  /* ── 搜索逻辑 ─────────────────────────── */

  async onSearch() {
    const { query, maxWide, depth, modeIndex, minScore } = this.data;
    const q = query.trim();

    if (!q) {
      wx.showToast({ title: '请输入搜索关键词', icon: 'none' });
      return;
    }

    this.setData({
      searching: true,
      error: null,
      result: null,
      transitionInfo: null,
      transitionReady: false,
    });

    try {
      // 构建设置 AP I URL
      const params = new URLSearchParams();
      params.set('q', q);
      params.set('max_wide', String(maxWide));
      params.set('depth', String(depth));
      params.set('min_score', String(minScore / 10));
      params.set('mode', this._getModeValue(modeIndex));

      const url = `${this.data.apiBase}/search/progressive?${params.toString()}`;

      const res = await new Promise((resolve, reject) => {
        wx.request({
          url,
          method: 'GET',
          success: (resp) => resolve(resp.data),
          fail: (err) => reject(err),
        });
      });

      if (res.code !== 0) {
        throw new Error(res.message || `搜索失败 (${res.code})`);
      }

      const resultData = res.data;
      const transitionInfo = resultData.transition || null;

      this.setData({
        result: resultData,
        transitionInfo,
        transitionReady: transitionInfo?.should_deep || false,
        searching: false,
      });

    } catch (err) {
      console.error('[ProgressiveSearch] 搜索失败:', err);
      this.setData({
        searching: false,
        error: err.message || '搜索请求失败，请检查网络连接',
      });
    }
  },

  /* ── 输入事件 ─────────────────────────── */

  onQueryInput(e) {
    this.setData({ query: e.detail.value });
  },

  /* ── 配置事件 ─────────────────────────── */

  toggleConfig() {
    this.setData({
      configExpanded: !this.data.configExpanded,
    });
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
    this.setData({ minScore: e.detail.value });
  },

  /* ── 工具函数 ─────────────────────────── */

  _getModeValue(index) {
    const modes = ['hybrid', 'score', 'count'];
    return modes[index] || 'hybrid';
  },

  /* ── 分享 ─────────────────────────────── */

  onShareAppMessage() {
    const { query } = this.data;
    return {
      title: query ? `渐进式人脉搜索: ${query}` : '渐进式人脉搜索',
      path: `/pages/progressive_search/index${query ? `?q=${encodeURIComponent(query)}` : ''}`,
    };
  },
});
