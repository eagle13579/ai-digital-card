const MockService = require('../../../utils/mockService')

Page({
  data: {
    nodeCount: 0,
    hasData: true,
  },

  nodes: [],
  edges: [],
  canvasCtx: null,
  canvasWidth: 0,
  canvasHeight: 0,
  dpr: 1,
  animationId: null,
  draggingNode: null,

  onLoad() {
    const saved = wx.getStorageSync('trust_network')
    if (saved && saved.length) {
      this.nodes = saved
      this.setData({
        nodeCount: this.nodes.length - 1, // exclude 'self'
        hasData: this.nodes.length > 1,
      })
    } else {
      this.loadData()
    }
  },

  onReady() {
    this.initCanvas()
    // renderGraph() is called inside initCanvas() after canvas dimensions are available
  },

  onShow() {
    if (this.animationId) {
      this.startAnimation()
    }
  },

  onHide() {
    this.stopAnimation()
  },

  onUnload() {
    this.stopAnimation()
  },

  loadData() {
    const trustNet = MockService.getTrustNetwork()
    const trusting = trustNet.trusting || []
    const trustedBy = trustNet.trustedBy || []
    const allContacts = [...trusting, ...trustedBy]
    
    this.nodes = [{
      id: 'self',
      name: '我',
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      radius: 30,
      isSelf: true,
    }]

    const angleStep = (Math.PI * 2) / Math.max(allContacts.length, 1)

    allContacts.forEach((contact, index) => {
      const angle = index * angleStep
      const distance = 100 + Math.random() * 50
      this.nodes.push({
        id: contact.id || `node_${index}`,
        name: contact.name || `联系人${index + 1}`,
        x: Math.cos(angle) * distance,
        y: Math.sin(angle) * distance,
        vx: 0,
        vy: 0,
        radius: 18,
        isSelf: false,
        data: contact,
      })
      this.edges.push({
        from: 'self',
        to: contact.id || `node_${index}`,
      })
    })

    this.setData({
      nodeCount: allContacts.length,
      hasData: allContacts.length > 0,
    })
  },

  initCanvas() {
    const query = wx.createSelectorQuery()
    query.select('#graphCanvas').node((res) => {
      const canvas = res.node
      if (!canvas) return
      
      const ctx = canvas.getContext('2d')
      
      query.select('.graph-canvas').boundingClientRect((rect2) => {
        if (!rect2) return
        this._canvasRect = rect2
        this.canvasWidth = rect2.width
        this.canvasHeight = rect2.height
        
        const sysInfo = wx.getDeviceInfo()
        this.dpr = sysInfo.pixelRatio || 2
        
        canvas.width = this.canvasWidth * this.dpr
        canvas.height = this.canvasHeight * this.dpr
        this.canvasCtx = ctx
        this.renderGraph()
      }).exec()
    }).exec()
  },

  renderGraph() {
    if (!this.canvasCtx) return

    const ctx = this.canvasCtx
    const dpr = this.dpr

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight)

    const centerX = this.canvasWidth / 2
    const centerY = this.canvasHeight / 2

    this.edges.forEach((edge) => {
      const fromNode = this.nodes.find(n => n.id === edge.from)
      const toNode = this.nodes.find(n => n.id === edge.to)
      if (!fromNode || !toNode) return

      ctx.beginPath()
      ctx.moveTo(centerX + fromNode.x, centerY + fromNode.y)
      ctx.lineTo(centerX + toNode.x, centerY + toNode.y)
      ctx.strokeStyle = 'rgba(139, 92, 246, 0.3)'
      ctx.lineWidth = 1.5
      ctx.stroke()
    })

    this.nodes.forEach((node) => {
      const x = centerX + node.x
      const y = centerY + node.y

      if (node.isSelf) {
        const gradient = ctx.createRadialGradient(x - 5, y - 5, 0, x, y, node.radius)
        gradient.addColorStop(0, '#a78bfa')
        gradient.addColorStop(0.5, '#8b5cf6')
        gradient.addColorStop(1, '#6d28d9')
        ctx.beginPath()
        ctx.arc(x, y, node.radius, 0, Math.PI * 2)
        ctx.fillStyle = gradient
        ctx.fill()

        ctx.beginPath()
        ctx.arc(x, y, node.radius + 4, 0, Math.PI * 2)
        ctx.strokeStyle = 'rgba(139, 92, 246, 0.4)'
        ctx.lineWidth = 2
        ctx.stroke()

        ctx.fillStyle = '#fff'
        ctx.font = '14px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText('我', x, y)
      } else {
        ctx.beginPath()
        ctx.arc(x, y, node.radius, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(30, 30, 50, 0.8)'
        ctx.fill()
        ctx.strokeStyle = 'rgba(139, 92, 246, 0.3)'
        ctx.lineWidth = 1
        ctx.stroke()

        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'
        ctx.font = '11px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText(node.name, x, y)
      }
    })
  },

  startAnimation() {
    const animate = () => {
      this.simulateForces()
      this.renderGraph()
      this.animationId = requestAnimationFrame(animate)
    }
    animate()
  },

  stopAnimation() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId)
      this.animationId = null
    }
  },

  simulateForces() {
    const centerX = this.canvasWidth / 2
    const centerY = this.canvasHeight / 2
    const damping = 0.9
    const repulsion = 5000
    const attraction = 0.05

    this.nodes.forEach((node) => {
      if (node.isSelf) return

      let fx = (centerX - (centerX + node.x)) * attraction
      let fy = (centerY - (centerY + node.y)) * attraction

      this.nodes.forEach((other) => {
        if (other.id === node.id) return
        const dx = node.x - other.x
        const dy = node.y - other.y
        const dist = Math.sqrt(dx * dx + dy * dy) + 10
        const force = repulsion / (dist * dist)
        fx += (dx / dist) * force
        fy += (dy / dist) * force
      })

      node.vx = (node.vx + fx) * damping
      node.vy = (node.vy + fy) * damping
      node.x += node.vx
      node.y += node.vy

      const maxDist = Math.min(this.canvasWidth, this.canvasHeight) / 3
      const distFromCenter = Math.sqrt(node.x * node.x + node.y * node.y)
      if (distFromCenter > maxDist) {
        node.x = (node.x / distFromCenter) * maxDist
        node.y = (node.y / distFromCenter) * maxDist
        node.vx *= 0.5
        node.vy *= 0.5
      }
    })
  },

  onTouchStart(e) {
    const touch = e.touches[0]
    const centerX = this.canvasWidth / 2
    const centerY = this.canvasHeight / 2

    for (let i = this.nodes.length - 1; i >= 0; i--) {
      const node = this.nodes[i]
      const dx = touch.clientX - (centerX + node.x)
      const dy = touch.clientY - (centerY + node.y)
      if (dx * dx + dy * dy <= node.radius * node.radius * 4) {
        this.draggingNode = node
        this.stopAnimation()
        break
      }
    }
  },

  onTouchMove(e) {
    if (!this.draggingNode) return
    const touch = e.touches[0]
    const centerX = this.canvasWidth / 2
    const centerY = this.canvasHeight / 2

    this.draggingNode.x = touch.clientX - centerX
    this.draggingNode.y = touch.clientY - centerY
    this.renderGraph()
  },

  onTouchEnd() {
    if (this.draggingNode) {
      this.draggingNode = null
      this.startAnimation()
    }
  },

  addContact() {
    wx.showModal({
      title: '添加联系人',
      editable: true,
      placeholderText: '请输入联系人姓名',
      success: (res) => {
        if (res.confirm && res.content) {
          const name = res.content.trim()
          if (name) {
            const angle = Math.random() * Math.PI * 2
            const distance = 100 + Math.random() * 50
            const newNode = {
              id: `node_${Date.now()}`,
              name,
              x: Math.cos(angle) * distance,
              y: Math.sin(angle) * distance,
              vx: 0,
              vy: 0,
              radius: 18,
              isSelf: false,
            }
            this.nodes.push(newNode)
            this.edges.push({ from: 'self', to: newNode.id })
            this.setData({ nodeCount: this.nodes.length - 1, hasData: true })
            wx.setStorageSync('trust_network', this.nodes)
            this.renderGraph()
            wx.showToast({ title: '添加成功', icon: 'success' })
          }
        }
      },
    })
  },

  importWechat() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  refreshGraph() {
    this.loadData()
    this.renderGraph()
    wx.showToast({ title: '图谱已刷新', icon: 'success' })
  },
})