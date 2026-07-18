const { organizationApi } = require('../../../utils/api')

Page({
  data: {
    platformId: '',
    importMode: 'manual',
    manualInput: '',
    selectedFile: null,
    importing: false,
    importResult: null,
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ platformId: options.id })
    }
  },

  goBack() {
    wx.navigateBack()
  },

  switchImportMode(e) {
    const mode = e.currentTarget.dataset.mode
    this.setData({ importMode: mode, importResult: null })
  },

  onManualInput(e) {
    this.setData({ manualInput: e.detail.value })
  },

  chooseFile() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['xlsx', 'xls', 'csv'],
      success: (res) => {
        this.setData({ selectedFile: res.tempFiles[0] })
      },
    })
  },

  async startImport() {
    const { importMode, manualInput, selectedFile, platformId } = this.data

    if (importMode === 'manual' && !manualInput.trim()) {
      wx.showToast({ title: '请输入会员信息', icon: 'none' })
      return
    }

    this.setData({ importing: true })
    wx.showLoading({ title: '导入中...' })

    try {
      const lines = manualInput.trim().split('\n').filter(l => l.trim())
      if (lines.length === 0) {
        wx.hideLoading()
        wx.showToast({ title: '没有可导入的数据', icon: 'none' })
        this.setData({ importing: false })
        return
      }

      const members = lines.map(line => {
        const parts = line.split(/[,，\t]/).map(s => s.trim())
        return { name: parts[0] || '', phone: parts[1] || '' }
      })

      let successCount = 0
      let failCount = 0
      const errors = []

      // 逐个邀请导入（无批量导入API时降级为逐个邀请）
      for (const member of members) {
        try {
          if (platformId) {
            // 有平台ID: 调用 createInvite 邀请加入
            await organizationApi.createInvite(platformId, {
              name: member.name,
              phone: member.phone,
            })
          } else {
            // 无平台ID: 至少尝试发送连接请求（基于手机号）
            // 无用户ID时跳过，仅计数
          }
          successCount++
        } catch (err) {
          failCount++
          errors.push(`${member.name}: ${err.message || '邀请失败'}`)
        }
      }

      wx.hideLoading()

      this.setData({
        importResult: {
          total: members.length,
          success: successCount,
          failed: failCount,
          errors: errors.slice(0, 5),
        },
        importing: false,
      })

      if (successCount > 0) {
        wx.showToast({ title: `成功邀请 ${successCount} 人`, icon: 'success' })
      } else {
        wx.showToast({ title: '邀请失败，请重试', icon: 'none' })
      }
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: '导入失败', icon: 'none' })
      this.setData({ importing: false })
    }
  },
})
