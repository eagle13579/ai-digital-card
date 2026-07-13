/**
 * 用户协议页面
 * AI数智名片 - 微信小程序
 */
Page({
  data: {},

  onLoad() {
    // 协议内容静态展示，无需额外加载
  },

  onShareAppMessage() {
    return {
      title: '用户协议 - AI数智名片',
      path: '/pages/agreement/user',
    }
  },
})
