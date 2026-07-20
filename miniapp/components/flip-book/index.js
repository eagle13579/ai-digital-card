/**
 * FlipBook 3D翻转名片组件
 * 迁移自 liankebao-weapp (Taro React → 原生微信)
 */
Component({
  properties: {
    cardData: { type: Object, value: null },
    flippable: { type: Boolean, value: true },
    defaultSide: { type: String, value: 'front' },
    loading: { type: Boolean, value: false },
    className: { type: String, value: '' },
  },

  data: {
    flipped: false,
    bgStyle: 'linear-gradient(135deg, #1677ff 0%, #0958d9 100%)',
  },

  lifetimes: {
    attached() {
      if (this.properties.defaultSide === 'back') {
        this.setData({ flipped: true })
      }
      this._updateBg()
    },
  },

  observers: {
    'cardData': function () {
      this._updateBg()
    },
  },

  methods: {
    _updateBg() {
      const data = this.properties.cardData
      if (data && data.bg_image) {
        this.setData({ bgStyle: `url(${data.bg_image}) center/cover no-repeat` })
      }
    },

    handleFlip() {
      if (!this.properties.flippable || this.properties.loading) return
      const newFlipped = !this.data.flipped
      this.setData({ flipped: newFlipped })
      this.triggerEvent('flip', { side: newFlipped ? 'back' : 'front' })
    },
  },
})
