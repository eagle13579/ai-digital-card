/**
 * 状态标记组件 - 在线/忙碌/离线
 *
 * 用法:
 * <status-badge status="online" />
 * <status-badge status="busy" text="忙碌" />
 */
const i18n = require('../../utils/i18n')

Component({
  properties: {
    status: {
      type: String,
      value: 'offline', // online | busy | offline
    },
    text: {
      type: String,
      value: '',
    },
    size: {
      type: String,
      value: 'small',  // small | medium
    },
  },

  data: {
    displayText: '',
    _t: {},
  },

  lifetimes: {
    attached() {
      this.setData({ _t: i18n.getTranslations() })
      this._updateText()
    },
  },

  observers: {
    'status, text': function () {
      this._updateText()
    },
  },

  methods: {
    _updateText() {
      const { status, text, _t } = this.data
      if (text) {
        this.setData({ displayText: text })
      } else {
        const map = {
          online: _t.statusOnline || '在线',
          busy: _t.statusBusy || '忙碌',
          offline: _t.statusOffline || '离线',
        }
        this.setData({ displayText: map[status] || '' })
      }
    },
  },
})
