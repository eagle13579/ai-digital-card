Component({
  properties: {
    currentUser: {
      type: Object,
      value: {},
    },
    trustList: {
      type: Array,
      value: [],
    },
  },

  data: {
    totalCount: 0,
    paths: [],
  },

  observers: {
    trustList(newVal) {
      this.setData({
        totalCount: newVal.length,
      })
      this.generatePaths(newVal)
    },
  },

  methods: {
    generatePaths(list) {
      if (!list || list.length === 0) {
        this.setData({ paths: [] })
        return
      }

      const centerX = 150
      const centerY = 100
      const radius = 60
      const count = Math.min(list.length, 8)
      const angleStep = (Math.PI * 2) / count

      const paths = []
      for (let i = 0; i < count; i++) {
        const angle = angleStep * i - Math.PI / 2
        const x = centerX + Math.cos(angle) * radius
        const y = centerY + Math.sin(angle) * radius

        paths.push({
          nodes: [{
            ...list[i],
            position: { x, y },
          }],
        })
      }

      this.setData({ paths })
    },

    onNodeTap(e) {
      const node = e.currentTarget.dataset.node
      if (node) {
        this.triggerEvent('nodeTap', { node })
      }
    },
  },
})
