/**
 * 路径显示组件
 * 可视化展示 A → B → C 的触达路径
 */
Component({
  properties: {
    path: {
      type: Array,
      value: [],
      observer: 'updateDisplay',
    },
    distance: {
      type: Number,
      value: -1,
    },
    message: {
      type: String,
      value: '',
    },
    visible: {
      type: Boolean,
      value: false,
    },
  },

  data: {
    displayNodes: [],
    showResult: false,
  },

  methods: {
    updateDisplay(path) {
      if (!path || path.length === 0) {
        this.setData({ displayNodes: [], showResult: false })
        return
      }
      const displayNodes = path.map((node, index) => ({
        ...node,
        index,
        isFirst: index === 0,
        isLast: index === path.length - 1,
        isMiddle: index > 0 && index < path.length - 1,
      }))
      this.setData({ displayNodes, showResult: true })
    },

    close() {
      this.setData({ visible: false, showResult: false })
      this.triggerEvent('close')
    },

    onNodeTap(e) {
      const { id, name } = e.currentTarget.dataset
      this.triggerEvent('nodetap', { id, name })
    },
  },
})
