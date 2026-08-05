/**
 * 可见性选择器组件
 * 4级可见性矩阵：公开 → 好友可见 → 2度人脉可见 → 仅自己
 */
Component({
  properties: {
    value: {
      type: String,
      value: 'public',
    },
    label: {
      type: String,
      value: '可见范围',
    },
    showLabel: {
      type: Boolean,
      value: true,
    },
  },

  data: {
    showPicker: false,
    levels: [
      { key: 'public', label: '🌍 公开可见', desc: '所有人可见', icon: 'public' },
      { key: 'friend', label: '👥 好友可见', desc: '仅好友可见', icon: 'friend' },
      { key: 'network', label: '🔗 2度人脉', desc: '好友及好友的好友可见', icon: 'network' },
      { key: 'private', label: '🔒 仅自己', desc: '仅自己可见', icon: 'private' },
    ],
    selectedLabel: '',
    selectedDesc: '',
  },

  lifetimes: {
    attached() {
      this.updateDisplay()
    },
  },

  observers: {
    'value': function () {
      this.updateDisplay()
    },
  },

  methods: {
    updateDisplay() {
      const level = this.data.levels.find(l => l.key === this.data.value)
      if (level) {
        this.setData({
          selectedLabel: level.label,
          selectedDesc: level.desc,
        })
      }
    },

    openPicker() {
      this.setData({ showPicker: true })
    },

    closePicker() {
      this.setData({ showPicker: false })
    },

    stopPropagation() {},

    selectLevel(e) {
      const key = e.currentTarget.dataset.key
      const level = this.data.levels.find(l => l.key === key)
      if (level) {
        this.setData({
          value: key,
          selectedLabel: level.label,
          selectedDesc: level.desc,
          showPicker: false,
        })
        this.triggerEvent('change', { value: key, ...level })
      }
    },
  },
})
