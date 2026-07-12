/**
 * 联系人导入页面
 * 支持：微信好友邀请 / 手动输入 / 扫码添加
 */
const { Logger } = require('../../../utils/util')
const store = require('../../../utils/store')

Page({
  data: {
    // ====== 导入方式 ======
    importMethods: [
      { key: 'wechat', icon: '💬', title: '微信好友', desc: '分享邀请链接给微信好友' },
      { key: 'manual', icon: '✍️', title: '手动输入', desc: '手动录入联系人信息' },
      { key: 'qrcode', icon: '📷', title: '扫码添加', desc: '扫描对方二维码名片' },
    ],
    activeMethod: '',

    // ====== 手动输入表单 ======
    name: '',
    phone: '',

    // ====== 已导入联系人列表 ======
    contacts: [],
    _contactsKey: 'imported_contacts',

    // ====== 分享配置 ======
    shareConfig: {
      title: '快来和我交换数智名片',
      desc: '使用AI数智名片，快速建立商务连接',
      path: '/pages/card/card',
    },
  },

  onLoad() {
    this._loadContacts()
  },

  onShareAppMessage() {
    const config = this.data.shareConfig
    return {
      title: config.title,
      desc: config.desc,
      path: config.path,
    }
  },

  // ==================== 联系人存储 ====================

  _loadContacts() {
    try {
      const saved = wx.getStorageSync(this.data._contactsKey)
      if (saved && Array.isArray(saved)) {
        this.setData({
          contacts: saved,
        })
      }
    } catch (e) {
      Logger.warn('导入联系人', '读取联系人失败', e)
    }
  },

  _saveContacts(contacts) {
    try {
      wx.setStorageSync(this.data._contactsKey, contacts)
    } catch (e) {
      Logger.warn('导入联系人', '保存联系人失败', e)
    }
  },

  // ==================== 导入方式选择 ====================

  selectMethod(e) {
    const key = e.currentTarget.dataset.key
    this.setData({
      activeMethod: key,
    })

    if (key === 'wechat') {
      this._shareToWechat()
    } else if (key === 'qrcode') {
      this._scanQR()
    }
    // manual: 停留在页面显示表单
  },

  // ==================== 微信好友邀请 ====================

  _shareToWechat() {
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline'],
      success: () => {
        Logger.info('导入联系人', '分享菜单已显示')
      },
    })

    wx.showToast({
      title: '点击右上角分享给好友',
      icon: 'none',
      duration: 3000,
    })
  },

  // ==================== 手动输入 ====================

  onNameInput(e) {
    this.setData({ name: e.detail.value })
  },

  onPhoneInput(e) {
    this.setData({ phone: e.detail.value })
  },

  saveManualContact() {
    const { name, phone } = this.data

    if (!name || !name.trim()) {
      wx.showToast({ title: '请输入联系人姓名', icon: 'none' })
      return
    }
    if (!phone || !phone.trim()) {
      wx.showToast({ title: '请输入手机号', icon: 'none' })
      return
    }

    // 简单的手机号验证
    const phoneRegex = /^1[3-9]\d{9}$/
    if (!phoneRegex.test(phone.trim())) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }

    const newContact = {
      id: `import_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      name: name.trim(),
      phone: phone.trim(),
      createdAt: Date.now(),
      source: 'manual',
    }

    const contacts = [...this.data.contacts, newContact]
    this._saveContacts(contacts)
    this.setData({
      contacts,
      name: '',
      phone: '',
    })

    wx.showToast({ title: '联系人已保存', icon: 'success' })
    Logger.info('导入联系人', '手动添加联系人成功', { name: newContact.name })
  },

  // ==================== 扫码添加 ====================

  _scanQR() {
    wx.scanCode({
      onlyFromCamera: false,
      scanType: ['qrCode', 'barCode'],
      success: (res) => {
        Logger.info('导入联系人', '扫码成功', { result: res.result })

        // 尝试解析扫码结果
        const scanResult = res.result || ''
        const newContact = {
          id: `import_scan_${Date.now()}`,
          name: scanResult.slice(0, 20) || '扫码联系人',
          phone: '',
          source: 'qrcode',
          scanResult: scanResult,
          createdAt: Date.now(),
        }

        const contacts = [...this.data.contacts, newContact]
        this._saveContacts(contacts)
        this.setData({ contacts })

        wx.showModal({
          title: '扫码成功',
          content: `已添加联系人：${newContact.name}\n可手动编辑完善信息`,
          showCancel: false,
        })
      },
      fail: (err) => {
        Logger.warn('导入联系人', '扫码失败', err)
        if (err.errMsg && err.errMsg.includes('cancel')) {
          // 用户取消扫码
          this.setData({ activeMethod: '' })
        } else {
          wx.showToast({ title: '扫码失败，请重试', icon: 'none' })
        }
      },
    })
  },

  // ==================== 联系人管理 ====================

  deleteContact(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '删除联系人',
      content: '确定要删除该联系人吗？',
      success: (res) => {
        if (res.confirm) {
          const contacts = this.data.contacts.filter(c => c.id !== id)
          this._saveContacts(contacts)
          this.setData({ contacts })
          wx.showToast({ title: '已删除', icon: 'success' })
        }
      },
    })
  },

  clearAllContacts() {
    if (this.data.contacts.length === 0) return
    wx.showModal({
      title: '清空联系人',
      content: '确定要清空所有已导入的联系人吗？',
      success: (res) => {
        if (res.confirm) {
          this._saveContacts([])
          this.setData({ contacts: [] })
          wx.showToast({ title: '已清空', icon: 'success' })
        }
      },
    })
  },

  goBack() {
    wx.navigateBack()
  },
})
