/**
 * 创建资源平台申请
 */
Page({
  data: {
    name: '',
    fee: '',
    agreed: false,
    submitting: false,
  },

  onNameInput(e) {
    this.setData({ name: e.detail.value })
  },
  onFeeInput(e) {
    this.setData({ fee: e.detail.value })
  },
  toggleAgree() {
    this.setData({ agreed: !this.data.agreed })
  },

  canSubmit() {
    return this.data.name.trim() && this.data.fee.trim() && this.data.agreed
  },

  submit() {
    if (!this.canSubmit()) {
      wx.showToast({ title: '请完善信息并同意协议', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    // Mock提交
    setTimeout(() => {
      wx.showToast({ title: '申请已提交', icon: 'success' })
      this.setData({ submitting: false })
      setTimeout(() => wx.navigateBack(), 1500)
    }, 1000)
  },

  goBack() {
    wx.navigateBack()
  },
})
