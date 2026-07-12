const { MockService } = require('../../../utils/mockService')
const { sixDegreesApi } = require('../../../utils/api')
const store = require('../../../utils/store')

// Polyfill requestAnimationFrame for WeChat mini-program (Canvas 2D context)
if (typeof requestAnimationFrame === 'undefined') {
  var requestAnimationFrame = function (cb) { return setTimeout(function () { cb(Date.now()) }, 16) }
  var cancelAnimationFrame = function (id) { clearTimeout(id) }
}

const ANIMATION_INTERVAL = 16
const MAX_NODES = 20

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
    // 节点信息弹窗
    showInfoModal: false,
    selectedNode: null,
    // 子网络导航
    isSubNetwork: false,
    subNetworkLabel: '',
  },

  nodes: [],
  edges: [],
  canvasCtx: null,
  canvasWidth: 0,
  canvasHeight: 0,
  dpr: 1,
  animationId: null,
  draggingNode: null,
  // 触摸位置追踪（用于区分点击/拖拽）
  _touchStartX: 0,
  _touchStartY: 0,
  _touchStartTime: 0,

  onLoad(options) {
    this.loadData()
  },

  onReady() {
    this.initCanvas()
    setTimeout(() => {
      if (this.nodes.length > 0) {
        this.renderGraph()
        this.startAnimation()
      }
    }, 300)
  },

  onShow() {
    if (this.canvasCtx && this.nodes.length > 0) {
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
      const state = store.getState()
      const userId = state.userInfo?.id || 'u001'

      if (MockService.USE_MOCK) {
        console.log('[Graph] 开始加载Mock数据（六度人脉）')
        const res = await MockService.getSixDegreesNetwork(userId)
        const data = res.data || res
        console.log('[Graph] 数据加载完成:', JSON.stringify(data))
        this._buildGraphFromSixDegrees(data)
        console.log('[Graph] 图谱构建完成:', this.nodes.length, 'nodes,', this.edges.length, 'edges')
      } else {
        console.log('[Graph] 开始加载真实API数据（六度人脉）')
        const res = await sixDegreesApi.network(userId)
        const data = res.data || res || { nodes: [], links: [] }
        this._buildGraphFromSixDegrees(data)
      }
    } catch (err) {
      console.error('[Graph] 加载数据失败:', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  /** 从六度人脉API数据构建图谱（nodes + links格式） */
  _buildGraphFromSixDegrees(data) {
    const rawNodes = data.nodes || []
    const rawLinks = data.links || []

    if (rawNodes.length === 0) {
      this.nodes = []
      this.edges = []
      this.setData({ nodeCount: 0, hasData: false })
      return
    }

    // Find the center node (group=0 / depth=0 or first node)
    const centerNode = rawNodes.find(n => n.depth === 0 || n.group === 0) || rawNodes[0]
    const centerId = centerNode.id

    this.stopAnimation()

    // Build node map from sixDegrees data
    const nodeMap = new Map()

    // Center node
    nodeMap.set(centerId, {
      id: centerId,
      name: centerNode.name || '我',
      company: centerNode.company || '',
      title: centerNode.title || '',
      avatar: centerNode.avatar || '',
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      radius: 30,
      isSelf: true,
      data: centerNode,
    })

    // Other nodes
    rawNodes.forEach((n) => {
      if (n.id === centerId) return
      if (nodeMap.has(n.id)) return
      const angle = Math.random() * Math.PI * 2
      const distance = 100 + Math.random() * 50
      nodeMap.set(n.id, {
        id: n.id,
        name: n.name || n.id,
        company: n.company || '',
        title: n.title || '',
        avatar: n.avatar || '',
        x: Math.cos(angle) * distance,
        y: Math.sin(angle) * distance,
        vx: 0,
        vy: 0,
        radius: 18,
        isSelf: false,
        data: n,
      })
    })

    // Build edges from links
    const edgeSet = new Set()
    const newEdges = []
    rawLinks.forEach((l) => {
      const src = l.source || l.from
      const tgt = l.target || l.to
      if (!src || !tgt) return
      const key = `${src}-${tgt}`
      if (edgeSet.has(key)) return
      edgeSet.add(key)
      edgeSet.add(`${tgt}-${src}`)
      if (nodeMap.has(src) && nodeMap.has(tgt)) {
        newEdges.push({
          from: src,
          to: tgt,
          relation: l.relation || '',
          trustScore: l.trustScore || 0,
        })
      }
    })

    this.nodes = Array.from(nodeMap.values())
    this.edges = newEdges

    this.setData({
      nodeCount: this.nodes.length - 1,
      hasData: this.nodes.length > 1,
    })

    if (this.canvasCtx) {
      this.renderGraph()
    } else {
      setTimeout(() => {
        if (this.canvasCtx) {
          this.renderGraph()
          this.startAnimation()
        }
      }, 500)
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

        const sysInfo = wx.getSystemInfoSync ? wx.getSystemInfoSync() : wx.getDeviceInfo()
        this.dpr = sysInfo.pixelRatio || 2

        canvas.width = this.canvasWidth * this.dpr
        canvas.height = this.canvasHeight * this.dpr
        this.canvasCtx = ctx
        this.renderGraph()
        if (this.nodes.length > 0) {
          this.startAnimation()
        }
      }).exec()
    }).exec()
  },

  renderGraph() {
    if (!this.canvasCtx) return
    if (!this.canvasWidth || !this.canvasHeight) return
    if (this.nodes.length === 0) return

    const ctx = this.canvasCtx
    const dpr = this.dpr
    const centerX = this.canvasWidth / 2
    const centerY = this.canvasHeight / 2

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight)

    ctx.strokeStyle = 'rgba(139, 92, 246, 0.2)'
    ctx.lineWidth = 1

    this.edges.forEach((edge) => {
      const fromNode = this.nodes.find(n => n.id === edge.from)
      const toNode = this.nodes.find(n => n.id === edge.to)
      if (!fromNode || !toNode) return
      ctx.beginPath()
      ctx.moveTo(centerX + fromNode.x, centerY + fromNode.y)
      ctx.lineTo(centerX + toNode.x, centerY + toNode.y)
      ctx.stroke()
    })

    this.nodes.forEach((node, index) => {
      const x = centerX + node.x
      const y = centerY + node.y

      if (node.isSelf) {
        ctx.beginPath()
        ctx.arc(x, y, node.radius, 0, Math.PI * 2)
        ctx.fillStyle = '#8b5cf6'
        ctx.fill()

        ctx.beginPath()
        ctx.arc(x, y, node.radius + 4, 0, Math.PI * 2)
        ctx.strokeStyle = 'rgba(139, 92, 246, 0.3)'
        ctx.lineWidth = 1.5
        ctx.stroke()

        ctx.fillStyle = '#fff'
        ctx.font = '12px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText('我', x, y)
      } else {
        ctx.beginPath()
        ctx.arc(x, y, node.radius, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(30, 30, 50, 0.9)'
        ctx.fill()
        ctx.strokeStyle = 'rgba(139, 92, 246, 0.2)'
        ctx.lineWidth = 0.5
        ctx.stroke()

        if (index % 2 === 0) {
          ctx.fillStyle = 'rgba(255, 255, 255, 0.6)'
          ctx.font = '10px sans-serif'
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          ctx.fillText(node.name, x, y + node.radius + 12)
        }
      }
    })
  },

  startAnimation() {
    if (this.animationId) return
    this._animFrameCount = 0
    this._isStable = false
    this._lastRenderTime = Date.now()
    const animate = () => {
      this._animFrameCount++
      if (this._animFrameCount % 4 === 0) {
        this.simulateForces()
      }
      const now = Date.now()
      if (now - this._lastRenderTime > 100) {
        this.renderGraph()
        this._lastRenderTime = now
      }
      if (!this._isStable && this._animFrameCount < 120) {
        this.animationId = requestAnimationFrame(animate)
      } else if (!this._isStable) {
        this._isStable = true
      }
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
    const damping = 0.96
    const repulsion = 2000
    const attraction = 0.02
    const maxInteractionDist = 150
    let totalVelocity = 0
    let movingCount = 0

    const nodeCount = this.nodes.length
    for (let i = 0; i < nodeCount; i++) {
      const node = this.nodes[i]
      if (node.isSelf) continue

      let fx = -node.x * attraction
      let fy = -node.y * attraction

      for (let j = 0; j < nodeCount; j++) {
        if (i === j) continue
        const other = this.nodes[j]
        const dx = node.x - other.x
        const dy = node.y - other.y
        const distSq = dx * dx + dy * dy
        if (distSq > maxInteractionDist * maxInteractionDist) continue
        const dist = Math.sqrt(distSq)
        const force = repulsion / (distSq + 100)
        const nx = dx / dist
        const ny = dy / dist
        fx += nx * force
        fy += ny * force
      }

      node.vx = (node.vx + fx) * damping
      node.vy = (node.vy + fy) * damping
      node.x += node.vx
      node.y += node.vy

      const maxDist = Math.min(this.canvasWidth, this.canvasHeight) / 3
      const distFromCenter = Math.sqrt(node.x * node.x + node.y * node.y)
      if (distFromCenter > maxDist) {
        const ratio = maxDist / distFromCenter
        node.x *= ratio
        node.y *= ratio
        node.vx *= 0.3
        node.vy *= 0.3
      }

      const velSq = node.vx * node.vx + node.vy * node.vy
      totalVelocity += Math.sqrt(velSq)
      if (velSq > 0.01) movingCount++
    }

    const avgVelocity = totalVelocity / Math.max(nodeCount - 1, 1)
    if (avgVelocity < 0.05 && movingCount < 2) {
      this._isStable = true
    }
  },

  onTouchStart(e) {
    const touch = e.touches[0]
    const canvasRect = this._canvasRect || { left: 0, top: 0 }
    const tx = touch.clientX - canvasRect.left
    const ty = touch.clientY - canvasRect.top
    const centerX = this.canvasWidth / 2
    const centerY = this.canvasHeight / 2

    // 记录触摸起始位置（用于区分点击/拖拽）
    this._touchStartX = tx
    this._touchStartY = ty
    this._touchStartTime = Date.now()

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

  onTouchEnd(e) {
    const wasDragging = this.draggingNode !== null

    if (this.draggingNode) {
      this.draggingNode = null
      this.startAnimation()
    }

    // 检测是否为"点击"而非拖拽：移动距离小且时间短
    if (!wasDragging) {
      const touch = e.changedTouches[0]
      if (touch) {
        const canvasRect = this._canvasRect || { left: 0, top: 0 }
        const tx = touch.clientX - canvasRect.left
        const ty = touch.clientY - canvasRect.top
        const dx = tx - this._touchStartX
        const dy = ty - this._touchStartY
        const distance = Math.sqrt(dx * dx + dy * dy)
        const duration = Date.now() - this._touchStartTime

        // 判断为点击：移动距离 < 10px 且 持续时间 < 300ms
        if (distance < 10 && duration < 300) {
          const hitNode = this._findNodeAtPosition(tx, ty)
          if (hitNode) {
            this.showNodeInfo(hitNode)
            return
          }
        }
      }
    }
  },

  _findNodeAtPosition(tx, ty) {
    const centerX = this.canvasWidth / 2
    const centerY = this.canvasHeight / 2
    for (let i = this.nodes.length - 1; i >= 0; i--) {
      const node = this.nodes[i]
      const dx = tx - (centerX + node.x)
      const dy = ty - (centerY + node.y)
      if (dx * dx + dy * dy <= node.radius * node.radius) {
        return node
      }
    }
    return null
  },

  // ====== 节点信息弹窗 ======

  showNodeInfo(node) {
    if (node.isSelf) {
      const userInfo = node.data || {}
      this.setData({
        showInfoModal: true,
        selectedNode: {
          id: node.id,
          name: node.name,
          avatar: userInfo.avatar || '',
          relation: '自己',
          trustScore: 100,
          isSelf: true,
        },
      })
      return
    }

    const contactData = node.data || {}
    this.setData({
      showInfoModal: true,
      selectedNode: {
        id: node.id,
        name: node.name,
        avatar: contactData.avatar || '',
        relation: contactData.relation || '联系人',
        trustScore: contactData.trustScore || 0,
        isSelf: false,
      },
    })
  },

  closeInfoModal() {
    this.setData({
      showInfoModal: false,
      selectedNode: null,
    })
  },

  stopPropagation() {
  },

  goBackToMainNetwork() {
    if (this._mainNetworkNodes && this._mainNetworkEdges) {
      this.nodes = JSON.parse(JSON.stringify(this._mainNetworkNodes))
      this.edges = JSON.parse(JSON.stringify(this._mainNetworkEdges))
      this._mainNetworkNodes = null
      this._mainNetworkEdges = null
      this._mainNetworkCenterId = null

      this.setData({
        isSubNetwork: false,
        subNetworkLabel: '',
      })

      this.renderGraph()
      this.startAnimation()
    } else {
      this.loadData()
    }
  },

  _rebuildGraphWithCenter(centerId, friends) {
    this.stopAnimation()

    const newNodeMap = new Map()

    const existingNode = this.nodes.find(n => n.id === centerId)
    const centerData = existingNode ? existingNode.data || {} : {}
    const centerName = existingNode ? existingNode.name : (centerId === 'self' ? '我' : centerId)

    newNodeMap.set(centerId, {
      id: centerId,
      name: centerName,
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      radius: 30,
      isSelf: true,
      data: centerData,
    })

    const angleStep = (Math.PI * 2) / Math.max(friends.length, 1)
    friends.forEach((friend, index) => {
      const friendId = friend.id !== undefined ? String(friend.id) : `node_${index}`
      if (newNodeMap.has(friendId)) return

      const angle = index * angleStep
      const distance = 100 + Math.random() * 50

      newNodeMap.set(friendId, {
        id: friendId,
        name: friend.name || `联系人${index + 1}`,
        x: Math.cos(angle) * distance,
        y: Math.sin(angle) * distance,
        vx: 0,
        vy: 0,
        radius: 18,
        isSelf: false,
        data: friend,
      })
    })

    const newEdges = []
    newNodeMap.forEach((node, id) => {
      if (id !== centerId) {
        newEdges.push({ from: centerId, to: id })
      }
    })

    this.nodes = Array.from(newNodeMap.values())
    this.edges = newEdges

    this.setData({
      nodeCount: this.nodes.length - 1,
      hasData: this.nodes.length > 1,
    })

    this.renderGraph()
    this.startAnimation()
  },

  // ====== BFS 触达路径查找 ======
  openPathSearch() {
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

  selectFriendTarget(e) {
    const { id, name } = e.currentTarget.dataset
    this.setData({ targetUserId: id })
    this.searchPath()
  },

  async searchPath() {
    const targetId = this.data.targetUserId.trim()
    if (!targetId) {
      return wx.showToast({ title: '请输入目标用户ID', icon: 'none' })
    }

    this.setData({ searchingPath: true })

    try {
      if (MockService.USE_MOCK) {
        const state = store.getState()
        const userId = state.userInfo?.id || 'u001'
        const result = await MockService.getSixDegreesPath(userId, targetId)
        this._handlePathResult(result)
      } else {
        const state = store.getState()
        const userId = state.userInfo?.id || 'u001'
        const res = await sixDegreesApi.path(userId, targetId)
        const result = res.data || res || { distance: -1, path: [] }
        this._handlePathResult(result)
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

  // ====== 建立关系 ======
  async createRelation() {
    wx.showModal({
      title: '建立六度人脉关系',
      content: '输入目标用户ID和关系描述',
      editable: true,
      placeholderText: '目标用户ID',
      success: async (res) => {
        if (res.confirm && res.content) {
          const targetUserId = res.content.trim()
          if (!targetUserId) return wx.showToast({ title: '请输入用户ID', icon: 'none' })

          wx.showModal({
            title: '关系类型',
            content: '输入关系描述（如：同事、朋友、合作伙伴）',
            editable: true,
            placeholderText: '关系描述',
            success: async (res2) => {
              if (!res2.confirm) return
              const relation = res2.content || '联系人'

              wx.showLoading({ title: '建立关系中...' })
              try {
                const state = store.getState()
                const userId = state.userInfo?.id || 'u001'
                const payload = {
                  user_id: userId,
                  target_user_id: targetUserId,
                  relation: relation,
                  trust_score: 80,
                }
                if (MockService.USE_MOCK) {
                  await MockService.createSixDegreesRelation(payload)
                } else {
                  await sixDegreesApi.createRelation(payload)
                }
                wx.hideLoading()
                wx.showToast({ title: '关系建立成功', icon: 'success' })
                // Refresh the graph
                this.refreshGraph()
              } catch (err) {
                wx.hideLoading()
                console.error('[Graph] 建立关系失败:', err)
                wx.showToast({ title: '建立失败', icon: 'none' })
              }
            },
          })
        }
      },
    })
  },

  _handlePathResult(result) {
    this.setData({
      searchingPath: false,
      pathResult: result,
      showPathResult: true,
    })

    if (result.path && result.path.length > 1) {
      this.highlightPath(result.path)
    }
  },

  highlightPath(pathNodes) {
    if (!this.canvasCtx) return

    const pathIds = new Set(pathNodes.map(n => n.id))
    const ctx = this.canvasCtx
    const dpr = this.dpr
    const centerX = this.canvasWidth / 2
    const centerY = this.canvasHeight / 2

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    this.renderGraph()

    this.nodes.forEach((node) => {
      if (!pathIds.has(node.id)) return
      const x = centerX + node.x
      const y = centerY + node.y

      ctx.beginPath()
      ctx.arc(x, y, node.radius + 6, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.6)'
      ctx.lineWidth = 3
      ctx.stroke()

      ctx.beginPath()
      ctx.arc(x, y, node.radius + 10, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.2)'
      ctx.lineWidth = 2
      ctx.stroke()
    })
  },

  onPathNodeTap(e) {
    const { id, name } = e.currentTarget.dataset
    console.log('[Graph] 路径节点点击:', id, name)
    wx.showToast({ title: `${name} (${id})`, icon: 'none' })
  },

  closePathResult() {
    this.setData({ showPathResult: false })
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

  async refreshGraph() {
    this.stopAnimation()
    await this.loadData()
    setTimeout(() => {
      this.renderGraph()
      this.startAnimation()
    }, 100)
    wx.showToast({ title: '图谱已刷新', icon: 'success' })
  },
})
