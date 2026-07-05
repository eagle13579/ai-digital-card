/**
 * 名片详情页
 * 展示单张名片的详细信息与统计数据
 * 增加：Free用户创建名片限制检查
 */
const { brochureApi, visitorApi, miniappApi, membershipApi } = require('../../utils/api')

Page({
  data: {
    loading: true,
    card: null,
    stats: { views: 0, visitors: 0, matches: 0, trust: 0 },
    purposeText: '',
  },

  onLoad(options) {
    const cardId = options.id
    if (cardId) {
      this.loadCardDetail(cardId)
    } else {
      // 无ID时检查会员限制
      this.checkCreateLimit()
    }
  },

  /**
   * 检查名片创建限制
   * Free用户最多创建1张名片，超出提示升级Pro
   */
  async checkCreateLimit() {
    this.setData({ loading: true })
    try {
      const membershipRes = await membershipApi.getStatus()
      const membership = membershipRes.data ?? membershipRes ?? {}
      const memberLevel = membership.tier || membership.level || 'free'
      const cardCount = membership.card_count ?? membership.cardCount ?? 0
      const cardLimit = membership.card_limit ?? membership.cardLimit ?? (memberLevel === 'free' ? 1 : 10)

      if (memberLevel === 'free' && cardCount >= cardLimit) {
        // 超出限制，弹窗提示升级
        wx.showModal({
          title: '升级Pro',
          content: `免费版仅支持${cardLimit}张名片，您已达到上限。升级Pro可创建最多10张名片！`,
          confirmText: '升级Pro',
          cancelText: '取消',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({ url: '/pages/membership/membership' })
            } else {
              wx.navigateBack()
            }
          },
        })
        this.setData({ loading: false })
      } else {
        // 未超限，跳转到创建页面
        wx.redirectTo({ url: '/pages/brochure/create/index' })
      }
    } catch (err) {
      console.error('检查创建限制失败:', err)
      // 降级：允许创建
      wx.redirectTo({ url: '/pages/brochure/create/index' })
    }
  },

  async loadCardDetail(cardId) {
    this.setData({ loading: true })
    try {
      const brochure = await brochureApi.getById(cardId)
      
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
        const vStats = await visitorApi.getStats(cardId)
        stats.views = vStats.view_count || 0
        stats.visitors = vStats.total_visits || 0
      }

      this.setData({
        card,
        stats,
        purposeText,
        loading: false,
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
})
