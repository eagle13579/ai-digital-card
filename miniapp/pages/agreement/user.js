Page({
  data: {},

  onLoad(options) {
    // 设置导航栏标题
    wx.setNavigationBarTitle({
      title: '用户协议',
    });
  },

  onShow() {
    // 页面显示时的逻辑
  },

  // 返回上一页
  handleBack() {
    wx.navigateBack({
      delta: 1,
    });
  },

  // 页面分享
  onShareAppMessage() {
    return {
      title: 'AI数智名片 - 用户协议',
      path: '/pages/agreement/user/user',
    };
  },
});
