const { MockService } = require('../../../utils/mockService')
const { listPlatforms } = require('../../../utils/platform-bridge')
const i18n = require('../../../utils/i18n')
Page({
  data: {
    loading: true,
    platforms: [],
    showEmpty: false,
    useRealApi: true,
  },

  onLoad() {
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const res = await listPlatforms({ keyword: '', skip: 0, limit: 20 }, this.data.useRealApi)
      const platforms = (res.data || []).map((p, index) => ({
        ...p,
        rank: index + 1,
        // 首字母logo
        logoLetter: p.name ? p.name[0] : 'P',
      }))
      this.setData({
        platforms,
        showEmpty: platforms.length === 0,
        loading: false,
      })
    } catch (err) {
      console.error('[PlatformList] 加载失败:', err)
      this.setData({
        loading: false,
        showEmpty: true,
      })
    }
  },

  goBack() {
    wx.navigateBack()
  },

  /** 跳转平台详情 */
  goDetail(e) {
    const id = e.currentTarget.dataset.id
    if (id) {
      wx.navigateTo({ url: `/pages/platform/detail/index?id=${id}` })
    }
  },

  /** 格式化年费 */
  formatFee(fee) {
    if (!fee && fee !== 0) return '待定'
    if (fee === 0) return '免费'
    return `¥${fee}/年`
  },
})
