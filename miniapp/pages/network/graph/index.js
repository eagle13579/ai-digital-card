/**
 * 人脉图谱 — Canvas 2D 力导向图
 */
const { MockService } = require('../../../utils/mockService')

// 力导向算法参数
const PHYSICS = {
  REPULSION: 3000,    // 节点间斥力强度
  ATTRACTION: 0.005,  // 边的弹力系数
  DAMPING: 0.85,      // 速度衰减
  CENTER_GRAVITY: 0.01, // 向心力
  MIN_SPEED: 0.3,     // 停止阈值
  ITERATIONS: 80,     // 最大迭代帧数
}

const COLORS = {
  bg: '#0a0a18',
  nodeBase: '#06b6d4',
  nodeMe: '#8b5cf6',
  edgeLine: 'rgba(139,92,246,0.15)',
  edgeMe: 'rgba(6,182,212,0.25)',
  textPrimary: '#e4e4ed',
  textSecondary: '#8b8b9e',
  glow: 'rgba(6,182,212,0.1)',
}

Page({

  data: {
    loading: true,
    nodeCount: 0,
    edgeCount: 0,
  },

  // ==================================================
  // 页面生命周期
  // ==================================================
  onLoad() {
    this.graphData = null
    this.nodes = []
    this.edges = []
    this.canvas = null
    this.ctx = null
    this.dpr = 1
    this.animFrame = null
    this.iteration = 0

    // 触摸状态
    this.touch = { x: 0, y: 0, dragging: false, draggedNode: null }
    this.pinch = { dist: 0, scale: 1 }

    this.loadGraphData()
  },

  onUnload() {
    if (this.animFrame) {
      this.animFrame = null
    }
  },

  onReady() {
    // Canvas 初始化延后到数据加载完成
  },

  // ==================================================
  // 数据加载
  // ==================================================
  async loadGraphData() {
    try {
      const profile = await MockService.getUserProfile()
      const profileData = profile.data !== undefined ? profile.data : profile
      const userName = profileData.name || '我'

      const trustRes = await MockService.getTrustNetwork()
      const contacts = trustRes.trusting ?? trustRes.data?.trusting ?? trustRes.data ?? []

      this.buildGraph(userName, contacts)
      this.setData({
        loading: false,
        nodeCount: this.nodes.length,
        edgeCount: this.edges.length,
      })

      this.initCanvas()

    } catch (err) {
      console.error('[人脉图谱] 加载失败:', err)
      this.setData({ loading: false, nodeCount: 0, edgeCount: 0 })
    }
  },

  // ==================================================
  // 构建图谱
  // ==================================================
  buildGraph(userName, contacts) {
    const nodes = []
    const edges = []
    const nodeMap = {}

    // 中心节点 = "我"
    const meId = '__me__'
    nodes.push({
      id: meId,
      label: userName || '我',
      sub: '当前用户',
      isMe: true,
      x: 0, y: 0,
      vx: 0, vy: 0,
      radius: 32,
    })
    nodeMap[meId] = true

    // 联系人节点
    const contactsArr = Array.isArray(contacts) ? contacts : []
    contactsArr.forEach((c, i) => {
      const nid = `c-${c.id || i}`
      nodes.push({
        id: nid,
        label: c.name || `联系人${i + 1}`,
        sub: [c.position, c.company].filter(Boolean).join(' · '),
        isMe: false,
        x: 0, y: 0,
        vx: 0, vy: 0,
        radius: 18,
        _contact: c,
      })
      nodeMap[nid] = true
      edges.push({ source: meId, target: nid })
    })

    // 如果有>2个联系人，在相似联系人之间也加边（同公司/同行业）
    if (contactsArr.length >= 3) {
      for (let i = 0; i < contactsArr.length; i++) {
        for (let j = i + 1; j < contactsArr.length; j++) {
          const ci = contactsArr[i]
          const cj = contactsArr[j]
          // 同公司加边
          if (ci.company && cj.company && ci.company === cj.company) {
            edges.push({ source: `c-${ci.id || i}`, target: `c-${cj.id || j}` })
          }
        }
      }
    }

    // 随机初始化位置（围绕中心散开）
    nodes.forEach((n) => {
      if (n.isMe) return // 中心节点在原点
      const angle = Math.random() * Math.PI * 2
      const dist = 80 + Math.random() * 120
      n.x = Math.cos(angle) * dist
      n.y = Math.sin(angle) * dist
    })

    this.nodes = nodes
    this.edges = edges
    this.graphData = { userName, contacts: contactsArr }
  },

  // ==================================================
  // Canvas 初始化
  // ==================================================
  initCanvas() {
    const query = wx.createSelectorQuery().in(this)
    query.select('#graphCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res || !res[0]) {
          console.warn('[人脉图谱] Canvas节点未找到')
          return
        }
        const canvasNode = res[0].node
        const width = res[0].width
        const height = res[0].height

        this.dpr = wx.getSystemInfoSync().pixelRatio
        canvasNode.width = width * this.dpr
        canvasNode.height = height * this.dpr

        this.canvas = canvasNode
        this.ctx = canvasNode.getContext('2d')
        this.canvasWidth = width
        this.canvasHeight = height

        // 缩放偏移
        this.offsetX = width / 2
        this.offsetY = height / 2
        this.scale = 1

        // 启动物理模拟
        this.startPhysics()
      })
  },

  // ==================================================
  // 力导向物理模拟
  // ==================================================
  startPhysics() {
    this.iteration = 0
    this.simulate()
  },

  simulate() {
    if (this.iteration >= PHYSICS.ITERATIONS) {
      this.render()
      return
    }

    const nodes = this.nodes
    const edges = this.edges
    const n = nodes.length

    // Step 1: 计算斥力（所有节点之间）
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const a = nodes[i]
        const b = nodes[j]
        let dx = b.x - a.x
        let dy = b.y - a.y
        let dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 5) {
          dx = Math.random() - 0.5
          dy = Math.random() - 0.5
          dist = 5
        }
        const force = PHYSICS.REPULSION / (dist * dist)
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force
        a.vx -= fx
        a.vy -= fy
        b.vx += fx
        b.vy += fy
      }
    }

    // Step 2: 计算引力（边两端互相吸引）
    edges.forEach((e) => {
      const a = nodes.find((n) => n.id === e.source)
      const b = nodes.find((n) => n.id === e.target)
      if (!a || !b) return
      const dx = b.x - a.x
      const dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const force = PHYSICS.ATTRACTION * dist
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force
      a.vx += fx
      a.vy += fy
      b.vx -= fx
      b.vy -= fy
    })

    // Step 3: 向心力（防止飞出去）
    nodes.forEach((n) => {
      if (n.isMe) return
      n.vx -= n.x * PHYSICS.CENTER_GRAVITY
      n.vy -= n.y * PHYSICS.CENTER_GRAVITY
    })

    // Step 4: 更新位置 + 阻尼
    let totalSpeed = 0
    nodes.forEach((n) => {
      n.vx *= PHYSICS.DAMPING
      n.vy *= PHYSICS.DAMPING
      n.x += n.vx
      n.y += n.vy
      totalSpeed += Math.sqrt(n.vx * n.vx + n.vy * n.vy)
    })

    this.iteration++

    // Step 5: 渲染当前帧
    this.render()

    // Step 6: 继续模拟（或停止）
    if (totalSpeed / n > PHYSICS.MIN_SPEED) {
      // 用 requestAnimationFrame
      this.canvas.requestAnimationFrame(() => this.simulate())
    }
  },

  // ==================================================
  // Canvas 渲染
  // ==================================================
  render() {
    const ctx = this.ctx
    const dpr = this.dpr
    const w = this.canvasWidth
    const h = this.canvasHeight
    const ox = this.offsetX
    const oy = this.offsetY
    const sc = this.scale

    // 清空
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height)
    ctx.scale(dpr, dpr)

    // 画边
    this.edges.forEach((e) => {
      const a = this.nodes.find((n) => n.id === e.source)
      const b = this.nodes.find((n) => n.id === e.target)
      if (!a || !b) return

      ctx.beginPath()
      ctx.moveTo(ox + a.x * sc, oy + a.y * sc)
      ctx.lineTo(ox + b.x * sc, oy + b.y * sc)

      if (a.isMe || b.isMe) {
        ctx.strokeStyle = COLORS.edgeMe
        ctx.lineWidth = 1.2
      } else {
        ctx.strokeStyle = COLORS.edgeLine
        ctx.lineWidth = 0.8
      }
      ctx.stroke()
    })

    // 画节点
    this.nodes.forEach((n) => {
      const cx = ox + n.x * sc
      const cy = oy + n.y * sc
      const r = n.radius * sc

      if (n.isMe) {
        // "我"节点 — 有发光效果
        const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, r * 2)
        gradient.addColorStop(0, COLORS.glow)
        gradient.addColorStop(1, 'transparent')
        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.arc(cx, cy, r * 2, 0, Math.PI * 2)
        ctx.fill()

        // 外圈
        ctx.beginPath()
        ctx.arc(cx, cy, r + 3, 0, Math.PI * 2)
        ctx.strokeStyle = 'rgba(139,92,246,0.3)'
        ctx.lineWidth = 1.5
        ctx.stroke()

        // 主体
        const ng = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.3, 0, cx, cy, r)
        ng.addColorStop(0, '#a78bfa')
        ng.addColorStop(1, '#8b5cf6')
        ctx.fillStyle = ng
        ctx.beginPath()
        ctx.arc(cx, cy, r, 0, Math.PI * 2)
        ctx.fill()

        // 文字：我
        ctx.fillStyle = '#fff'
        ctx.font = `bold ${Math.max(11, 14 * sc)}px sans-serif`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText('我', cx, cy + 1)

      } else {
        // 联系人节点
        const ng = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.3, 0, cx, cy, r)
        ng.addColorStop(0, '#38bdf8')
        ng.addColorStop(1, '#06b6d4')
        ctx.fillStyle = ng
        ctx.beginPath()
        ctx.arc(cx, cy, r, 0, Math.PI * 2)
        ctx.fill()

        // 光晕
        ctx.shadowColor = 'rgba(6,182,212,0.15)'
        ctx.shadowBlur = 8
        ctx.fill()
        ctx.shadowBlur = 0
      }
    })

    // 画标签（在节点下方）
    this.nodes.forEach((n) => {
      const cx = ox + n.x * sc
      const cy = oy + n.y * sc
      const r = n.radius * sc

      // 名字
      ctx.fillStyle = COLORS.textPrimary
      ctx.font = `${Math.max(10, 11 * sc)}px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillText(n.label.length > 6 ? n.label.slice(0, 6) + '..' : n.label, cx, cy + r + 4)

      // 副标题（如果有）
      if (n.sub && sc > 0.7) {
        ctx.fillStyle = COLORS.textSecondary
        ctx.font = `${Math.max(8, 9 * sc)}px sans-serif`
        ctx.fillText(n.sub.length > 8 ? n.sub.slice(0, 8) + '..' : n.sub, cx, cy + r + 18 * sc + 4)
      }
    })

    // 恢复缩放
    ctx.setTransform(1, 0, 0, 1, 0, 0)
  },

  // ==================================================
  // 触摸交互
  // ==================================================
  getTouchPos(touch) {
    const query = wx.createSelectorQuery().in(this)
    // 直接在事件中计算
    return { x: touch.x, y: touch.y }
  },

  findNodeAt(x, y) {
    const ox = this.offsetX
    const oy = this.offsetY
    const sc = this.scale
    // 从后往前遍历（上层节点优先）
    for (let i = this.nodes.length - 1; i >= 0; i--) {
      const n = this.nodes[i]
      const cx = ox + n.x * sc
      const cy = oy + n.y * sc
      const r = n.radius * sc + 8 // 加8px容差
      const dx = x - cx
      const dy = y - cy
      if (dx * dx + dy * dy <= r * r) {
        return n
      }
    }
    return null
  },

  onTouchStart(e) {
    if (e.touches.length === 1) {
      const touch = e.touches[0]
      const node = this.findNodeAt(touch.x, touch.y)
      this.tapTarget = node || null
      this.tapStartTime = Date.now()
      this.tapStartX = touch.x
      this.tapStartY = touch.y
      if (node) {
        this.touch.dragging = true
        this.touch.draggedNode = node
        this.touch.x = touch.x
        this.touch.y = touch.y
      }
    } else if (e.touches.length === 2) {
      // 双指缩放开始
      const t1 = e.touches[0], t2 = e.touches[1]
      this.pinch.dist = Math.sqrt(
        (t1.x - t2.x) * (t1.x - t2.x) + (t1.y - t2.y) * (t1.y - t2.y)
      )
    }
  },

  onTouchMove(e) {
    if (e.touches.length === 1 && this.touch.dragging && this.touch.draggedNode) {
      // 拖拽节点
      const touch = e.touches[0]
      const dx = (touch.x - this.touch.x) / this.scale
      const dy = (touch.y - this.touch.y) / this.scale
      this.touch.draggedNode.x += dx
      this.touch.draggedNode.y += dy
      this.touch.x = touch.x
      this.touch.y = touch.y
      this.render()
    } else if (e.touches.length === 2) {
      // 双指缩放
      const t1 = e.touches[0], t2 = e.touches[1]
      const dist = Math.sqrt(
        (t1.x - t2.x) * (t1.x - t2.x) + (t1.y - t2.y) * (t1.y - t2.y)
      )
      if (this.pinch.dist > 0) {
        const delta = dist / this.pinch.dist
        this.scale = Math.max(0.4, Math.min(2.5, this.scale * delta))
        this.render()
      }
      this.pinch.dist = dist
    }
  },

  onTouchEnd(e) {
    this.touch.dragging = false
    this.touch.draggedNode = null
    this.pinch.dist = 0
    // 点击检测：移动距离小于10px视为点击
    if (e && e.changedTouches && e.changedTouches.length > 0) {
      const deltaX = Math.abs(e.changedTouches[0].x - this.tapStartX)
      const deltaY = Math.abs(e.changedTouches[0].y - this.tapStartY)
      if (deltaX < 10 && deltaY < 10 && this.tapTarget) {
        const node = this.tapTarget
        // 中心节点（"我"）不跳转
        if (node.isMe) return
        // 提取真实联系人ID（node.id格式为 c-{contactId}）
        const contactId = node._contact?.brochureId || node._contact?.id
        if (contactId) {
          wx.navigateTo({ url: `/pages/card/card?id=${contactId}` })
        }
      }
    }
  },

  // ==================================================
  // 导航
  // ==================================================
  goBack() {
    const pages = getCurrentPages()
    if (pages.length > 1) {
      wx.navigateBack()
    } else {
      wx.switchTab({ url: '/pages/index/index' })
    }
  },
})
