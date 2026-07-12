const MockService = require('../../../utils/mockService')
const { BFSFinder } = require('../../../utils/bfs')

// Polyfill requestAnimationFrame for WeChat mini-program (Canvas 2D context)
if (typeof requestAnimationFrame === 'undefined') {
  var requestAnimationFrame = function (cb) { return setTimeout(function () { cb(Date.now()) }, 16) }
  var cancelAnimationFrame = function (id) { clearTimeout(id) }
}

Page({
  data: {
    nodeCount: 0,
    hasData: true,
    // BFS相关
    showPathSearch: false,
    targetUserId: '',
    searchingPath: false,
    pathResult: null,
    showPathResult: false,
    // 好友列表
    friendList: [],
    loadingFriends: false,
    searchMode: 'navigate', // navigate | quick
  },

  nodes: [],
  edges: [],
  canvasCtx: null,
  canvasWidth: 0,
  canvasHeight: 0,
  dpr: 1,
  animationId: null,
  draggingNode: null,

  onLoad(options) {
    // 支持外部传入nodes数据
    if (options.data && options.nodes) {
      this.nodes = options.nodes
      this.buildEdgesFromNodes()
      this.setData({
        nodeCount: this.nodes.length - 1,
        hasData: this.nodes.length > 1,
      })
    } else {
      const saved = wx.getStorageSync('trust_network')
      if (saved && saved.length) {
        this.nodes = saved
        this.setData({
          nodeCount: this.nodes.length - 1,
          hasData: this.nodes.length > 1,
        })
      } else {
        this.loadData()
      }
    }
  },

  onReady() {
    this.initCanvas()
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

  // ====== 数据加载 ======
  async loadData() {
    try {
      const trustNet = await MockService.getTrustNetwork()
      const data = trustNet.data || trustNet
      const trusting = data.trusting || []
      const trustedBy = data.trusted_by || []
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

      if (this.canvasCtx) {
        this.renderGraph()
      }
    } catch (err) {
      console.error('[Graph] 加载数据失败:', err)
    }
  },

  buildEdgesFromNodes() {
    this.edges = []
    this.nodes.forEach((node) => {
      if (!node.isSelf) {
        this.edges.push({ from: 'self', to: node.id })
      }
    })
  },

  // 加载好友列表（用于BFS前端快速选择）
  async loadFriendList() {
    this.setData({ loadingFriends: true })
    try {
      const friends = await MockService.getFriendsList('self')
      this.setData({
        friendList: friends || [],
        loadingFriends: false,
      })
    } catch (err) {
      console.error('[Graph] 加载好友列表失败:', err)
      this.setData({ loadingFriends: false })
    }
  },

  // ====== Canvas 渲染 ======
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
    const canvasRect = this._canvasRect || { left: 0, top: 0 }
    const tx = touch.clientX - canvasRect.left
    const ty = touch.clientY - canvasRect.top
    const centerX = this.canvasWidth / 2
    const centerY = this.canvasHeight / 2

    for (let i = this.nodes.length - 1; i >= 0; i--) {
      const node = this.nodes[i]
      const dx = tx - (centerX + node.x)
      const dy = ty - (centerY + node.y)
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
    const canvasRect = this._canvasRect || { left: 0, top: 0 }
    const tx = touch.clientX - canvasRect.left
    const ty = touch.clientY - canvasRect.top
    const centerX = this.canvasWidth / 2
    const centerY = this.canvasHeight / 2

    this.draggingNode.x = tx - centerX
    this.draggingNode.y = ty - centerY
    this.renderGraph()
  },

  onTouchEnd() {
    if (this.draggingNode) {
      this.draggingNode = null
      this.startAnimation()
    }
  },

  // ====== BFS 触达路径查找 ======
  openPathSearch() {
    this.loadFriendList()
    this.setData({
      showPathSearch: true,
      targetUserId: '',
      pathResult: null,
    })
  },

  closePathSearch() {
    this.setData({
      showPathSearch: false,
      pathResult: null,
    })
  },

  onTargetInput(e) {
    this.setData({ targetUserId: e.detail.value })
  },

  // 选择好友列表中的人作为目标
  selectFriendTarget(e) {
    const { id, name } = e.currentTarget.dataset
    this.setData({ targetUserId: id })
    // 自动搜索
    this.searchPath()
  },

  async searchPath() {
    const targetId = this.data.targetUserId.trim()
    if (!targetId) {
      return wx.showToast({ title: '请输入目标用户ID', icon: 'none' })
    }

    this.setData({ searchingPath: true })

    try {
      const result = await MockService.findPath(targetId)
      this.setData({
        searchingPath: false,
        pathResult: result,
        showPathResult: true,
      })

      // 如果找到路径，高亮节点
      if (result.path && result.path.length > 1) {
        this.highlightPath(result.path)
      }
    } catch (err) {
      console.error('[Graph] BFS搜索失败:', err)
      this.setData({
        searchingPath: false,
        pathResult: { distance: -1, path: [], message: '搜索失败，请重试' },
        showPathResult: true,
      })
    }
  },

  // 高亮路径节点
  highlightPath(pathNodes) {
    if (!this.canvasCtx) return

    const pathIds = new Set(pathNodes.map(n => n.id))
    const ctx = this.canvasCtx
    const dpr = this.dpr
    const centerX = this.canvasWidth / 2
    const centerY = this.canvasHeight / 2

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    this.renderGraph()

    // 在路径节点外围绘制发光圈
    this.nodes.forEach((node) => {
      if (!pathIds.has(node.id)) return
      const x = centerX + node.x
      const y = centerY + node.y

      ctx.beginPath()
      ctx.arc(x, y, node.radius + 6, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.6)'
      ctx.lineWidth = 3
      ctx.stroke()

      // 添加发光效果
      ctx.beginPath()
      ctx.arc(x, y, node.radius + 10, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.2)'
      ctx.lineWidth = 2
      ctx.stroke()
    })
  },

  // 路径节点点击
  onPathNodeTap(e) {
    const { id, name } = e.detail
    console.log('[Graph] 路径节点点击:', id, name)
    wx.showToast({ title: `${name} (${id})`, icon: 'none' })
  },

  closePathResult() {
    this.setData({ showPathResult: false })
    // 重新渲染普通图谱
    this.renderGraph()
  },

  // ====== 联系人管理 ======
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
