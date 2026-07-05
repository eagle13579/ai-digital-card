/**
 * 我的 - 个人中心/会员信息/设置
 * 连接后端真实API，替换所有mock数据
 * 增加：会员层级显示、使用额度(OCR/名片数)、Pro金色徽章、升级按钮
 */
const { userApi, subscriptionApi, messageApi, visitorApi, trustApi, brochureApi, membershipApi } = require('../../utils/api')

Page({
  data: {
    loading: true,
    userInfo: {},
    memberLevel: 'free',
    memberLevelText: 'Free',
    memberExpire: '',
    trustCount: 0,
    newVisitorCount: 0,
    stats: { visitors: 0, matches: 0, unlocks: 0, views: 0 },
    // 使用额度
    usage: {
      card_count: 0,
      card_limit: 1,
      ocr_count: 0,
      ocr_limit: 3,
    },
    isPro: false,
  },

  onLoad() {
    this.loadProfile()
  },

  onShow() {
    if (!this.data.loading) {
      this.loadProfile()
    }
  },

  async loadProfile() {
    this.setData({ loading: true })
    try {
      // 并发请求：用户信息、订阅信息、会员状态、信任网络、未读消息
      const [profileRes, subscriptionRes, membershipRes, trustRes, unreadRes] = await Promise.all([
        userApi.getProfile(),
        subscriptionApi.getCurrent(),
        membershipApi.getStatus().catch(() => null),
        trustApi.getNetwork(),
        messageApi.getUnreadCount(),
      ])

      // 兼容 { data: ... } 包裹和直接返回两种格式
      const profile = profileRes.data ?? profileRes
      const subscription = subscriptionRes.data ?? subscriptionRes
      const membership = membershipRes?.data ?? membershipRes ?? {}
      const trustNet = trustRes.data ?? trustRes
      const unread = unreadRes.data ?? unreadRes

      // 会员等级（优先级: membership > profile > subscription）
      const memberLevel = membership.tier || membership.level || profile.member_level || subscription?.plan || 'free'
      const memberLevelText = { free: 'Free', pro: 'Pro', enterprise: 'Enterprise' }[memberLevel] || 'Free'
      const isPro = memberLevel === 'pro' || memberLevel === 'enterprise'

      // 使用额度（从会员状态获取）
      const usage = {
        card_count: membership.card_count ?? membership.cardCount ?? 0,
        card_limit: membership.card_limit ?? membership.cardLimit ?? (memberLevel === 'free' ? 1 : 10),
        ocr_count: membership.ocr_count ?? membership.ocrCount ?? 0,
        ocr_limit: membership.ocr_limit ?? membership.ocrLimit ?? (memberLevel === 'free' ? 3 : 100),
      }

      // 信任网络人数
      const trustCount = (trustNet.trusting || []).length

      // 未读消息数（兼容不同字段名）
      const newVisitorCount = unread?.count ?? unread?.unread_count ?? 0

      // 获取画册列表 → 取第一个画册的访客统计
      let stats = { visitors: 0, matches: 0, unlocks: 0, views: 0 }
      try {
        const brochuresRes = await brochureApi.list({ page: 1, page_size: 5 })
        const brochures = brochuresRes.data ?? brochuresRes?.list ?? brochuresRes?.items ?? []
        if (brochures.length > 0) {
          const brochureId = brochures[0].id || brochures[0]._id
          const statsRes = await visitorApi.getStats(brochureId)
          const statsData = statsRes.data ?? statsRes
          stats = {
            visitors: statsData.total_visits ?? statsData.visitors ?? 0,
            matches: statsData.matches ?? statsData.match_count ?? 0,
            unlocks: statsData.unlocks ?? statsData.unlock_count ?? 0,
            views: statsData.views ?? statsData.view_count ?? statsData.total_views ?? 0,
          }
        }
      } catch (e) {
        console.warn('获取画册/访客数据失败:', e)
      }

      // 组装用户信息
      const userInfo = {
        id: profile.id || profile._id,
        name: profile.name || profile.nickname || '',
        avatar: profile.avatar || profile.avatar_url || '',
        company: profile.company || '',
        title: profile.title || profile.position || '',
      }

      this.setData({
        userInfo,
        memberLevel,
        memberLevelText,
        memberExpire: membership.expire_at || membership.expire_date || profile.member_expire || subscription?.expire_at || subscription?.expire_date || '',
        trustCount,
        newVisitorCount,
        stats,
        usage,
        isPro,
        loading: false,
      })

      // 同步到全局
      const app = getApp()
      if (typeof app.updateUserInfo === 'function') app.updateUserInfo(userInfo)
      if (typeof app.updateMemberLevel === 'function') app.updateMemberLevel(memberLevel)
    } catch (err) {
      console.error('加载个人数据失败:', err)
      this.setData({ loading: false })
    }
  },

  // 编辑名片
  goEditCard() {
    wx.navigateTo({ url: '/pages/brochure/create/index' })
  },

  // 画册管理
  goAlbum() {
    wx.navigateTo({ url: '/pages/brochure/create/index' })
  },

  // 会员中心
  goMember() {
    wx.navigateTo({ url: '/pages/membership/membership' })
  },

  // 访客记录
  goVisitorLog() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  // 信任网络
  goTrustNetwork() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  // 隐私设置
  goPrivacy() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  // 关于
  goAbout() {
    wx.showToast({ title: 'AI数智名片 v1.0.0', icon: 'none' })
  },

  // 退出登录
  logout() {
    wx.showModal({
      title: '确认退出',
      content: '退出后需要重新登录',
      success: (res) => {
        if (res.confirm) {
          const app = getApp()
          app.clearLogin()
          wx.reLaunch({ url: '/pages/index/index' })
        }
      },
    })
  },

  // 跳转修改资料页面
  goEditProfile() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  // 保存资料（API调用）
  async saveProfile(data) {
    try {
      const res = await userApi.updateProfile(data)
      wx.showToast({ title: '保存成功', icon: 'success' })
      this.loadProfile()
      return res
    } catch (err) {
      console.error('保存资料失败:', err)
      wx.showToast({ title: '保存失败', icon: 'none' })
      throw err
    }
  },
})
