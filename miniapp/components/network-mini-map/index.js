/**
 * 人脉链微地图组件 — NetworkMiniMap
 * =============================================
 * 极小尺寸角标展示名片人脉链路径
 * 3节点+箭头 canvas渲染，点击展开弹窗
 *
 * 调用后端: POST /api/v1/network/bridge
 */
const { networkApi } = require('../../utils/api')

Component({
  properties: {
    /** 当前用户ID */
    currentUserId: {
      type: String,
      value: '',
    },
    /** 目标名片用户ID */
    targetUserId: {
      type: String,
      value: '',
    },
    /** 名片分享token（兜底查询） */
    shareToken: {
      type: String,
      value: '',
    },
  },

  data: {
    /** 人脉链数据 */
    paths: [],
    /** 是否有路径数据 */
    hasPath: false,
    /** 是否展开弹窗 */
    expanded: false,
    /** 是否加载中 */
    loading: false,
    /** 选中中间人查看 */
    selectedNode: null,
    /** 弹窗显示选中的中间人 */
    showNodePreview: false,
    /** canvas尺寸 */
    miniWidth: 240,
    miniHeight: 160,
    expandWidth: 600,
    expandHeight: 400,
    /** 动画帧id */
    animFrameId: null,
  },

  observers: {
    'currentUserId, targetUserId': function (fromId, toId) {
      if (fromId && toId && fromId !== toId) {
        this.loadNetworkPath(fromId, toId)
      }
    },
  },

  lifetimes: {
    detached() {
      this.cancelAnimation()
    },
  },

  methods: {
    /** 加载人脉链路径 */
    async loadNetworkPath(fromId, toId) {
      this.setData({ loading: true })
      try {
        const res = await networkApi.bridge(fromId, toId)
        const paths = res && (res.paths || res.data?.paths || [])
        if (paths && paths.length > 0) {
          this.setData({
            paths,
            hasPath: true,
            loading: false,
          })
          // 渲染迷你图
          wx.nextTick(() => {
            this.drawMiniMap()
          })
        } else {
          this.setData({ hasPath: false, loading: false })
        }
      } catch (err) {
        console.warn('[NetworkMiniMap] 加载人脉链失败', err)
        this.setData({ hasPath: false, loading: false })
      }
    },

    /** 点击迷你图展开弹窗 */
    onTapExpand() {
      this.setData({
        expanded: true,
        showNodePreview: false,
        selectedNode: null,
      })
      wx.nextTick(() => {
        this.drawExpandedMap()
      })
    },

    /** 关闭弹窗 */
    onClosePopup() {
      this.setData({ expanded: false, showNodePreview: false })
      this.cancelAnimation()
    },

    /** 阻止冒泡 */
    noop() {},

    /** 点击中间人节点预览 */
    onNodeTap(e) {
      const node = e.currentTarget.dataset.node
      if (!node || !node.name) return
      // 脱敏显示
      this.setData({
        selectedNode: {
          name: this.maskName(node.name),
          relation: node.relation || '间接人脉',
          trustLevel: node.trust_level || '未知',
        },
        showNodePreview: true,
      })
    },

    /** 脱敏处理 */
    maskName(name) {
      if (!name) return '***'
      if (name.length <= 1) return '*'
      if (name.length === 2) return name[0] + '*'
      return name[0] + '**' + name[name.length - 1]
    },

    /** 关闭节点预览 */
    onCloseNodePreview() {
      this.setData({ showNodePreview: false, selectedNode: null })
    },

    /** 绘制迷你图 */
    drawMiniMap() {
      const query = this.createSelectorQuery()
      query.select('#miniMapCanvas')
        .fields({ node: true, size: true })
        .exec((res) => {
          if (!res || !res[0]) return
          const canvas = res[0].node
          const ctx = canvas.getContext('2d')
          const dpr = wx.getSystemInfoSync().pixelRatio
          const width = this.data.miniWidth
          const height = this.data.miniHeight
          canvas.width = width * dpr
          canvas.height = height * dpr
          ctx.scale(dpr, dpr)

          this.renderPath(ctx, width, height, this.data.paths[0], false)
        })
    },

    /** 绘制展开图 */
    drawExpandedMap() {
      const query = this.createSelectorQuery()
      query.select('#expandMapCanvas')
        .fields({ node: true, size: true })
        .exec((res) => {
          if (!res || !res[0]) return
          const canvas = res[0].node
          const ctx = canvas.getContext('2d')
          const dpr = wx.getSystemInfoSync().pixelRatio
          const width = this.data.expandWidth
          const height = this.data.expandHeight
          canvas.width = width * dpr
          canvas.height = height * dpr
          ctx.scale(dpr, dpr)

          this.renderPath(ctx, width, height, this.data.paths[0], true)
        })
    },

    /** 渲染路径（通用） */
    renderPath(ctx, w, h, path, isExpanded) {
      if (!path || !path.nodes || path.nodes.length < 2) return

      const nodes = path.nodes
      const count = Math.min(nodes.length, 3) // 最多显示3个节点
      const padding = isExpanded ? 60 : 20
      const nodeRadius = isExpanded ? 28 : 12
      const fontSize = isExpanded ? 14 : 0 // 迷你图不显示文字
      const arrowSize = isExpanded ? 10 : 5

      // 暗色背景
      ctx.clearRect(0, 0, w, h)

      // 节点位置（分布于水平中线）
      const stepX = (w - padding * 2) / (count - 1 || 1)
      const centerY = h / 2
      const points = nodes.slice(0, count).map((node, i) => ({
        x: padding + stepX * i,
        y: centerY,
        node,
      }))

      // 绘制连接线 + 箭头
      for (let i = 0; i < points.length - 1; i++) {
        const p1 = points[i]
        const p2 = points[i + 1]

        // 绘制线
        ctx.beginPath()
        ctx.moveTo(p1.x, p1.y)
        ctx.lineTo(p2.x, p2.y)
        ctx.strokeStyle = isExpanded
          ? 'rgba(139, 92, 246, 0.5)'
          : 'rgba(139, 92, 246, 0.4)'
        ctx.lineWidth = isExpanded ? 3 : 1.5
        ctx.stroke()

        // 绘制箭头
        const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x)
        const arrowX = p2.x - nodeRadius - 4
        const arrowY = p2.y
        ctx.beginPath()
        ctx.moveTo(arrowX, arrowY)
        ctx.lineTo(
          arrowX - arrowSize * Math.cos(angle - 0.4),
          arrowY - arrowSize * Math.sin(angle - 0.4)
        )
        ctx.lineTo(
          arrowX - arrowSize * Math.cos(angle + 0.4),
          arrowY - arrowSize * Math.sin(angle + 0.4)
        )
        ctx.closePath()
        ctx.fillStyle = 'rgba(139, 92, 246, 0.6)'
        ctx.fill()
      }

      // 绘制节点
      points.forEach((p, idx) => {
        // 光晕
        const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, nodeRadius * 2)
        glow.addColorStop(0, 'rgba(139, 92, 246, 0.2)')
        glow.addColorStop(1, 'rgba(139, 92, 246, 0)')
        ctx.fillStyle = glow
        ctx.beginPath()
        ctx.arc(p.x, p.y, nodeRadius * 2, 0, Math.PI * 2)
        ctx.fill()

        // 节点圆形
        const gradient = ctx.createRadialGradient(p.x - nodeRadius * 0.3, p.y - nodeRadius * 0.3, 0, p.x, p.y, nodeRadius)
        if (idx === 0) {
          // 起点 — 青色
          gradient.addColorStop(0, '#22d3ee')
          gradient.addColorStop(1, '#06b6d4')
        } else if (idx === count - 1) {
          // 终点 — 紫色
          gradient.addColorStop(0, '#a78bfa')
          gradient.addColorStop(1, '#8b5cf6')
        } else {
          // 中间节点 — 紫灰
          gradient.addColorStop(0, 'rgba(139, 92, 246, 0.6)')
          gradient.addColorStop(1, 'rgba(139, 92, 246, 0.3)')
        }
        ctx.beginPath()
        ctx.arc(p.x, p.y, nodeRadius, 0, Math.PI * 2)
        ctx.fillStyle = gradient
        ctx.fill()

        // 节点边框
        ctx.strokeStyle = idx === count - 1
          ? 'rgba(167, 139, 250, 0.6)'
          : 'rgba(255, 255, 255, 0.15)'
        ctx.lineWidth = 1.5
        ctx.stroke()

        // 展开模式显示文字
        if (isExpanded && p.node.name) {
          ctx.fillStyle = 'rgba(255, 255, 255, 0.7)'
          ctx.font = '12px sans-serif'
          ctx.textAlign = 'center'
          ctx.fillText(this.maskName(p.node.name), p.x, p.y + nodeRadius + 20)
        }
      })
    },

    /** 取消动画 */
    cancelAnimation() {
      if (this.data.animFrameId) {
        // canvas.cancelAnimationFrame
        this.setData({ animFrameId: null })
      }
    },
  },
})
