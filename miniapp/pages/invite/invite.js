Page({
  data: { code: '', codeError: '', verified: false, loading: false },
  onLoad() {},
  onCodeInput(e) {
    this.setData({ code: e.detail.value.toUpperCase(), codeError: '' });
  },
  async onVerify() {
    const { code } = this.data;
    if (!code || code.length !== 8) {
      this.setData({ codeError: '请输入8位邀请码' });
      return;
    }
    this.setData({ loading: true });
    try {
      const res = await wx.request({
        url: 'https://card.liankebao.top/api/v1/invite/verify',
        method: 'POST', data: { code }
      });
      if (res.data && res.data.valid) {
        this.setData({ verified: true, loading: false });
        wx.showToast({ title: '验证通过', icon: 'success' });
        wx.setStorageSync('invite_code', code);
      }
    } catch(e) {
      this.setData({ codeError: '邀请码无效', loading: false });
    }
  },
  onStart() {
    wx.reLaunch({ url: '/pages/login/login' });
  }
});
