/**
 * 名片详情页
 * 展示单张名片的详细信息与统计数据
 */
const { MockService } = require('../../utils/mockService')
const { miniappApi } = require('../../utils/api')

Page({
  data: {
    loading: true,
    card: null,
    stats: { views: 0, visitors: 0, matches: 0, trust: 0 },
    purposeText: '',
    showNetworkMap: true,
    currentUserId: '',
  },

  onLoad(options) {
    // 获取当前用户ID
    const userInfo = wx.getStorageSync('userInfo')
    if (userInfo && userInfo.id) {
      this.setData({ currentUserId: userInfo.id })
    } else if (getApp().globalData && getApp().globalData.userInfo) {
      this.setData({ currentUserId: getApp().globalData.userInfo.id })
    }
    const cardId = options.id
    if (cardId) {
      this.loadCardDetail(cardId)
    } else {
      // 无ID时检查会员限制
      this.checkCreateLimit()
    }
  },

  async checkCreateLimit() {
    this.setData({ loading: true })
    wx.redirectTo({ url: '/pages/brochure/create/index' })
  },

  async loadCardDetail(cardId) {
    this.setData({ loading: true })
    try {
      const brochure = await MockService.getBrochureById(cardId)
      
      let card = null
      if (brochure) {
        card = {
          id: brochure.id,
          user_id: brochure.user_id,
          title: brochure.title,
          cover: brochure.cover,
          purpose: brochure.purpose,
          status: brochure.status,
          share_token: brochure.share_token,
          view_count: brochure.view_count || 0,
          user_name: brochure.user_name || brochure.name || '',
          user_company: brochure.user_company || brochure.company || '',
          user_title: brochure.user_title || brochure.title || '',
          user_avatar: brochure.user_avatar || brochure.avatar || '',
        }
      }

      const purposeText = {
        partner: '寻找合作伙伴',
        investor: '寻找投资',
        employee: '寻找人才',
        client: '寻找客户',
        friend: '社交交友',
      }[card && card.purpose] || (card && card.purpose) || ''

      let stats = { views: 0, visitors: 0, matches: 0, trust: 0 }
      if (card) {
        const vStats = await MockService.getVisitorStats(cardId)
        const vStatsData = vStats.data !== undefined ? vStats.data : vStats
        stats.views = vStatsData.view_count || 0
        stats.visitors = vStatsData.total_visits || 0
      }

      this.setData({
        card,
        stats,
        purposeText,
        loading: false,
        showNetworkMap: true,
      })
    } catch (err) {
      console.error('加载名片详情失败:', err)
      this.setData({ loading: false })
    }
  },

  // 预览
  goPreview() {
    if (this.data.card) {
      wx.navigateTo({ url: `/pages/preview/index?id=${this.data.card.id}` })
    }
  },

  // 分享
  shareCard() {
    wx.showShareMenu({ withShareTicket: true })
  },

  // 生成小程序码
  async generateQRCode() {
    if (!this.data.card?.share_token) {
      wx.showToast({ title: '该名片暂不支持生成二维码', icon: 'none' })
      return
    }
    wx.showLoading({ title: '生成中...' })
    try {
      const result = await miniappApi.getQRCode(this.data.card.share_token)
      if (result && result.tempFilePath) {
        wx.hideLoading()
        wx.previewImage({ urls: [result.tempFilePath] })
      } else if (result instanceof ArrayBuffer) {
        // 如果返回二进制图片数据
        const fs = wx.getFileSystemManager()
        const filePath = `${wx.env.USER_DATA_PATH}/qrcode_${this.data.card.share_token}.png`
        fs.writeFile({
          filePath,
          data: result,
          encoding: 'binary',
          success() {
            wx.hideLoading()
            wx.previewImage({ urls: [filePath] })
          },
          fail() {
            wx.hideLoading()
            wx.showToast({ title: '二维码生成失败', icon: 'none' })
          },
        })
      } else {
        wx.hideLoading()
        wx.showToast({ title: '二维码生成成功', icon: 'success' })
      }
    } catch (err) {
      wx.hideLoading()
      console.error('生成二维码失败:', err)
    }
  },

  onShareAppMessage() {
    const card = this.data.card
    return {
      title: card?.title || 'AI数智名片',
      path: card ? `/pages/preview/index?id=${card.id}` : '/pages/index/index',
    }
  },

  // 人脉链中间人点击 - 跳转到中间人名片预览
  onConnectTap(e) {
    const { userId, userName } = e.detail || {}
    if (userId) {
      wx.navigateTo({
        url: `/pages/card/card?id=${userId}`,
      })
    }
  },
})
