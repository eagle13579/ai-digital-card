// pages/ai/config/index.js — AI客服配置 (占位页)
// 功能：AI客服功能开关与自定义配置

Page({
  data: {
    settings: {
      autoReply: true,
      smartRecommend: true,
      dataAnalysis: false,
      filterSensitive: true,
      timeout: 30,
      welcomeMessage: '您好！我是AI智能客服，请问有什么可以帮您的？'
    }
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: '客服配置' });
  },

  onToggle(e) {
    const key = e.currentTarget.dataset.key;
    const value = e.detail.value;
    this.setData({
      [`settings.${key}`]: value
    });
  },

  onWelcomeInput(e) {
    this.setData({
      'settings.welcomeMessage': e.detail.value
    });
  },

  onSave() {
    // 模拟保存
    wx.showLoading({ title: '保存中...' });
    setTimeout(() => {
      wx.hideLoading();
      wx.showToast({
        title: '配置已保存',
        icon: 'success'
      });
    }, 800);
  },

  goBack() {
    wx.navigateBack({
      delta: 1,
      fail: () => {
        wx.switchTab({ url: '/pages/index/index' });
      }
    });
  }
});
