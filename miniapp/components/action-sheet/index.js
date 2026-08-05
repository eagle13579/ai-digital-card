/**
 * 底部操作面板组件
 *
 * 用法:
 * <action-sheet visible="{{true}}" items="{{actions}}" bind:select="onActionSelect" bind:close="onClose" />
 */
Component({
  properties: {
    visible: {
      type: Boolean,
      value: false,
    },
    title: {
      type: String,
      value: '',
    },
    items: {
      type: Array,
      value: [],
    },
    showCancel: {
      type: Boolean,
      value: true,
    },
    cancelText: {
      type: String,
      value: '',
    },
  },

  methods: {
    onSelect(e) {
      const index = e.currentTarget.dataset.index
      const item = this.properties.items[index]
      this.triggerEvent('select', { index, item })
      this.close()
    },

    onClose() {
      this.close()
    },

    close() {
      this.setData({ visible: false })
      this.triggerEvent('close')
    },

    /** 阻止遮罩点击穿透 */
    noop() {
      // do nothing
    },
  },
})
