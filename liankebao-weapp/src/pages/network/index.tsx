import { FC, useState, useEffect, useCallback, useRef } from 'react'
import { View, Text, Canvas, Button } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { graphApi, GraphNode, GraphEdge } from '../../api/digitalBrochure'
import { api } from '../../api/client'
import { getShareLimitText, incrementShareCount } from '../../utils/share'
import './index.scss'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

type PageStatus = 'loading' | 'ready' | 'error' | 'empty'

type NodeType = 'person' | 'company' | 'industry' | 'tag' | 'center'

/** 力导向图节点（含物理坐标） */
interface ForceNode {
  id: string
  name: string
  type: NodeType
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  isCenter: boolean
  company?: string
  avatar?: string
  match_score?: number
  connectionCount: number
  raw: GraphNode
}

/** 力导向图边 */
interface ForceEdge {
  source: number // node index
  target: number // node index
  type: GraphEdge['type']
  weight: number
  label?: string
}

/** 选中的节点信息 */
interface SelectedNode {
  node: ForceNode
  relations: string[]
}

/** 图谱洞察数据（来自 insights API） */
interface GraphInsights {
  centrality_score?: number
  connection_count?: number
  industry_count?: number
  industry_distribution?: Record<string, number>
  influence_score?: number
  connection_trend?: string
}

/* ========================================================================== */
/*  常量                                                                       */
/* ========================================================================== */

const NODE_COLORS: Record<NodeType, string> = {
  person: '#3B82F6',
  company: '#10B981',
  industry: '#8B5CF6',
  tag: '#F59E0B',
  center: '#F59E0B',
}

const EDGE_STYLES: Record<GraphEdge['type'], { color: string; lineWidth: number; dash: number[] }> = {
  matched: { color: '#3B82F6', lineWidth: 1.5, dash: [] },
  trusted: { color: '#10B981', lineWidth: 2.5, dash: [] },
  works_at: { color: '#94A3B8', lineWidth: 1, dash: [6, 4] },
  same_industry: { color: '#8B5CF6', lineWidth: 1, dash: [4, 4] },
  tagged_as: { color: '#F59E0B', lineWidth: 0.8, dash: [] },
}

const CENTER_RADIUS = 30
const MIN_NODE_RADIUS = 20
const MAX_NODE_RADIUS = 28

// 物理参数
const REPULSION_STRENGTH = 8000
const SPRING_STIFFNESS = 0.005
const SPRING_REST_LENGTH = 180
const CENTER_GRAVITY = 0.01
const DAMPING = 0.85
const MIN_VELOCITY = 0.1
const MAX_ITERATIONS = 200
const STABLE_THRESHOLD = 0.5

const CANVAS_ID = 'networkCanvas'

const EDGE_LABELS: Record<GraphEdge['type'], string> = {
  matched: '匹配',
  trusted: '信任',
  works_at: '任职',
  same_industry: '同行业',
  tagged_as: '标签',
}

const LEGEND_ITEMS: { type: NodeType; label: string }[] = [
  { type: 'person', label: '人脉' },
  { type: 'company', label: '公司' },
  { type: 'industry', label: '行业' },
  { type: 'tag', label: '标签' },
]

/** 筛选按钮选项 */
const FILTER_ITEMS: { key: string; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'person', label: '人脉' },
  { key: 'company', label: '公司' },
  { key: 'industry', label: '行业' },
  { key: 'tag', label: '标签' },
]

/* ========================================================================== */
/*  辅助函数                                                                   */
/* ========================================================================== */

/** 获取节点名称缩写（取前2个字符） */
function getAbbr(name: string): string {
  if (!name) return '?'
  return name.slice(0, 2)
}

/** 按类型筛选图谱数据（保留中心节点） */
function filterGraphData(
  data: { nodes: GraphNode[]; edges: GraphEdge[] },
  filter: string,
): { nodes: GraphNode[]; edges: GraphEdge[] } {
  if (filter === 'all') return data
  const filteredNodes = data.nodes.filter((n) => {
    if (n.isCenter) return true
    return n.type === filter
  })
  const validIds = new Set(filteredNodes.map((n) => n.id))
  const filteredEdges = data.edges.filter(
    (e) => validIds.has(e.source) && validIds.has(e.target),
  )
  return { nodes: filteredNodes, edges: filteredEdges }
}

/** 计算节点间距离 */
function distance(a: { x: number; y: number }, b: { x: number; y: number }): number {
  const dx = a.x - b.x
  const dy = a.y - b.y
  return Math.sqrt(dx * dx + dy * dy)
}

/** 像素转DP */
function pxToDpr(px: number, dpr: number): number {
  return px * dpr
}

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Network: FC = () => {
  /* ---- 状态 ---- */
  const [status, setStatus] = useState<PageStatus>('loading')
  const [errorMsg, setErrorMsg] = useState('')
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null)
  const [connCount, setConnCount] = useState(0)
  const [relationCount, setRelationCount] = useState(0)
  const [insights, setInsights] = useState<GraphInsights | null>(null)
  const [filterType, setFilterType] = useState<string>('all')
  const [showStats, setShowStats] = useState(false)

  /* ---- Refs ---- */
  const canvasRef = useRef<any>(null)
  const contextRef = useRef<CanvasRenderingContext2D | null>(null)
  const dprRef = useRef(1)
  const sizeRef = useRef({ width: 0, height: 0 })
  const nodesRef = useRef<ForceNode[]>([])
  const edgesRef = useRef<ForceEdge[]>([])
  const animFrameRef = useRef<number>(0)
  const isDraggingRef = useRef(false)
  const dragNodeIdxRef = useRef(-1)
  const dragOffsetRef = useRef({ x: 0, y: 0 })
  const iterationRef = useRef(0)
  const stableRef = useRef(false)
  const rawDataRef = useRef<{ nodes: GraphNode[]; edges: GraphEdge[] } | null>(null)

  /* ---- 加载图谱数据 ---- */
  const loadGraph = useCallback(async () => {
    setStatus('loading')
    setErrorMsg('')
    try {
      const userId = Taro.getStorageSync('userId')
      if (!userId) {
        setStatus('empty')
        return
      }
      const res = await graphApi.getNetwork(userId)
      const data = res.data
      if (!data || !data.nodes || data.nodes.length === 0) {
        setStatus('empty')
        return
      }
      rawDataRef.current = data
      const filtered = filterGraphData(data, filterType)
      initGraph(filtered)
      setStatus('ready')

      // 异步加载图谱洞察数据
      api.get<any>(`/api/v1/knowledge-graph/insights/${userId}`)
        .then((insRes) => {
          if (insRes.data) setInsights(insRes.data)
        })
        .catch(() => {
          // 洞察数据为增强信息，加载失败不影响主流程
        })
    } catch (e: any) {
      setErrorMsg(e.message || '加载人脉网络失败')
      setStatus('error')
    }
  }, [])

  /* ---- 初始化图谱数据 ---- */
  const initGraph = useCallback((data: { nodes: GraphNode[]; edges: GraphEdge[] }) => {
    const { width, height } = sizeRef.current
    const cx = width / 2
    const cy = height / 2

    // 统计连接数
    const connMap: Record<string, number> = {}
    data.edges.forEach((edge) => {
      connMap[edge.source] = (connMap[edge.source] || 0) + 1
      connMap[edge.target] = (connMap[edge.target] || 0) + 1
    })

    // 构建节点
    const nodes: ForceNode[] = data.nodes.map((n, i) => {
      const isCenter = !!n.isCenter
      const conn = connMap[n.id] || 0
      const radius = isCenter
        ? CENTER_RADIUS
        : Math.max(MIN_NODE_RADIUS, Math.min(MAX_NODE_RADIUS, 16 + conn * 2))

      // 初始位置：中心节点在中心，其他随机分布在周围
      let x: number, y: number
      if (isCenter) {
        x = cx
        y = cy
      } else {
        const angle = (2 * Math.PI * i) / data.nodes.length + Math.random() * 0.5
        const dist = 150 + Math.random() * 100
        x = cx + Math.cos(angle) * dist
        y = cy + Math.sin(angle) * dist
      }

      return {
        id: n.id,
        name: n.label || n.name || '',
        type: isCenter ? 'center' : (n.type as NodeType),
        x,
        y,
        vx: 0,
        vy: 0,
        radius,
        isCenter,
        company: n.company,
        avatar: n.avatar,
        match_score: n.match_score,
        connectionCount: conn,
        raw: n,
      }
    })

    // 构建边（使用节点索引）
    const nodeIdxMap: Record<string, number> = {}
    nodes.forEach((n, i) => { nodeIdxMap[n.id] = i })

    const edges: ForceEdge[] = data.edges
      .filter((e) => nodeIdxMap[e.source] !== undefined && nodeIdxMap[e.target] !== undefined)
      .map((e) => ({
        source: nodeIdxMap[e.source],
        target: nodeIdxMap[e.target],
        type: (e.relation || e.type) as GraphEdge['type'],
        weight: e.weight || 0.5,
        label: e.label,
      }))

    nodesRef.current = nodes
    edgesRef.current = edges
    iterationRef.current = 0
    stableRef.current = false

    // 统计信息
    const personCount = nodes.filter((n) => n.type === 'person' || n.type === 'center').length
    const uniqueRelations = new Set(edges.map((e) => e.type))
    setConnCount(personCount)
    setRelationCount(uniqueRelations.size)
  }, [])

  /* ---- Canvas初始化 ---- */
  const initCanvas = useCallback(() => {
    Taro.createSelectorQuery()
      .select(`#${CANVAS_ID}`)
      .node()
      .exec((res) => {
        if (!res || !res[0] || !res[0].node) return
        const canvas = res[0].node
        canvasRef.current = canvas

        const ctx = canvas.getContext('2d')
        contextRef.current = ctx

        const dpr = Taro.getSystemInfoSync().pixelRatio || 2
        dprRef.current = dpr

        const sysInfo = Taro.getSystemInfoSync()
        const width = sysInfo.windowWidth
        const height = sysInfo.windowHeight
        sizeRef.current = { width, height }

        canvas.width = width * dpr
        canvas.height = height * dpr
        canvas.style.width = width + 'px'
        canvas.style.height = height + 'px'

        ctx.scale(dpr, dpr)

        // 加载数据
        loadGraph()
      })
  }, [loadGraph])

  /* ---- 物理模拟 ---- */
  const simulate = useCallback(() => {
    const nodes = nodesRef.current
    const edges = edgesRef.current
    const { width, height } = sizeRef.current
    const cx = width / 2
    const cy = height / 2

    if (nodes.length === 0) return

    let totalMovement = 0

    // 库仑排斥力（所有节点之间）
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i]
        const b = nodes[j]
        const dx = a.x - b.x
        const dy = a.y - b.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const force = REPULSION_STRENGTH / (dist * dist)
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force
        a.vx += fx
        a.vy += fy
        b.vx -= fx
        b.vy -= fy
      }
    }

    // 边弹簧吸引力
    for (const edge of edges) {
      const a = nodes[edge.source]
      const b = nodes[edge.target]
      const dx = b.x - a.x
      const dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const displacement = dist - SPRING_REST_LENGTH
      const force = SPRING_STIFFNESS * displacement
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force
      a.vx += fx
      a.vy += fy
      b.vx -= fx
      b.vy -= fy
    }

    // 中心引力
    for (const node of nodes) {
      const dx = cx - node.x
      const dy = cy - node.y
      node.vx += dx * CENTER_GRAVITY
      node.vy += dy * CENTER_GRAVITY
    }

    // 速度阻尼 + 位置更新
    for (const node of nodes) {
      node.vx *= DAMPING
      node.vy *= DAMPING

      // 停止微小的抖动
      if (Math.abs(node.vx) < MIN_VELOCITY && Math.abs(node.vy) < MIN_VELOCITY) {
        node.vx = 0
        node.vy = 0
      }

      node.x += node.vx
      node.y += node.vy

      totalMovement += Math.abs(node.vx) + Math.abs(node.vy)

      // 边界约束
      const margin = 40
      if (node.x < margin) { node.x = margin; node.vx = 0 }
      if (node.x > width - margin) { node.x = width - margin; node.vx = 0 }
      if (node.y < margin) { node.y = margin; node.vy = 0 }
      if (node.y > height - margin) { node.y = height - margin; node.vy = 0 }
    }

    // 稳定检测
    iterationRef.current++
    if (totalMovement < STABLE_THRESHOLD || iterationRef.current >= MAX_ITERATIONS) {
      stableRef.current = true
    }
  }, [])

  /* ---- 渲染画布 ---- */
  const render = useCallback(() => {
    const ctx = contextRef.current
    const nodes = nodesRef.current
    const edges = edgesRef.current
    const { width, height } = sizeRef.current
    if (!ctx || nodes.length === 0) return

    // 清空
    ctx.clearRect(0, 0, width, height)

    // ---- 绘制边 ----
    for (const edge of edges) {
      const a = nodes[edge.source]
      const b = nodes[edge.target]
      const style = EDGE_STYLES[edge.type] || EDGE_STYLES.matched
      const lineWidth = Math.max(0.3, Math.min(2, edge.weight))

      ctx.beginPath()
      ctx.moveTo(a.x, a.y)
      ctx.lineTo(b.x, b.y)
      ctx.strokeStyle = style.color
      ctx.lineWidth = lineWidth
      ctx.setLineDash(style.dash)
      ctx.stroke()
      ctx.setLineDash([])
    }

    // ---- 绘制节点 ----
    for (const node of nodes) {
      const color = NODE_COLORS[node.type] || '#666'

      // 外发光（中心节点）
      if (node.isCenter) {
        ctx.beginPath()
        ctx.arc(node.x, node.y, node.radius + 8, 0, 2 * Math.PI)
        ctx.fillStyle = 'rgba(245, 158, 11, 0.15)'
        ctx.fill()

        ctx.beginPath()
        ctx.arc(node.x, node.y, node.radius + 4, 0, 2 * Math.PI)
        ctx.fillStyle = 'rgba(245, 158, 11, 0.25)'
        ctx.fill()
      }

      // 圆形
      ctx.beginPath()
      ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI)

      if (node.isCenter) {
        const grad = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, node.radius)
        grad.addColorStop(0, '#FCD34D')
        grad.addColorStop(1, '#F59E0B')
        ctx.fillStyle = grad
      } else {
        ctx.fillStyle = color
      }
      ctx.fill()

      // 边框
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)'
      ctx.lineWidth = 1.5
      ctx.stroke()

      // 文字（名字缩写）
      ctx.fillStyle = '#ffffff'
      ctx.font = `bold ${Math.max(10, node.radius * 0.6)}px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(getAbbr(node.name), node.x, node.y)

      // 节点上方显示 label
      ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'bottom'
      ctx.fillText(node.name, node.x, node.y - node.radius - 4)
    }
  }, [])

  /* ---- 动画循环 ---- */
  const loop = useCallback(() => {
    if (stableRef.current) {
      render()
      return
    }

    simulate()
    render()

    if (!stableRef.current) {
      animFrameRef.current = requestAnimationFrame(loop)
    }
  }, [simulate, render])

  /* ---- 启动动画 ---- */
  const startAnimation = useCallback(() => {
    stableRef.current = false
    iterationRef.current = 0
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current)
    }
    loop()
  }, [loop])

  /* ---- 查找点击的节点 ---- */
  const findHitNode = useCallback((x: number, y: number): number => {
    const nodes = nodesRef.current
    for (let i = nodes.length - 1; i >= 0; i--) {
      const node = nodes[i]
      const dist = distance(node, { x, y })
      if (dist <= node.radius + 8) {
        return i
      }
    }
    return -1
  }, [])

  /* ---- 触控事件：touchstart ---- */
  const handleTouchStart = useCallback((e: any) => {
    const touch = e.touches[0]
    if (!touch) return
    const rect = Taro.createSelectorQuery().select(`#${CANVAS_ID}`).boundingClientRect()
    rect.exec((res) => {
      if (!res || !res[0]) return
      const canvasLeft = res[0].left
      const canvasTop = res[0].top
      const x = touch.clientX - canvasLeft
      const y = touch.clientY - canvasTop

      const idx = findHitNode(x, y)
      if (idx >= 0) {
        // 开始拖拽
        isDraggingRef.current = true
        dragNodeIdxRef.current = idx
        const node = nodesRef.current[idx]
        dragOffsetRef.current = { x: x - node.x, y: y - node.y }
      } else {
        // 点击空白区域取消选中
        setSelectedNode(null)
      }
    })
  }, [findHitNode])

  /* ---- 触控事件：touchmove ---- */
  const handleTouchMove = useCallback((e: any) => {
    if (!isDraggingRef.current || dragNodeIdxRef.current < 0) return
    e.preventDefault()

    const touch = e.touches[0]
    if (!touch) return

    const rect = Taro.createSelectorQuery().select(`#${CANVAS_ID}`).boundingClientRect()
    rect.exec((res) => {
      if (!res || !res[0]) return
      const canvasLeft = res[0].left
      const canvasTop = res[0].top
      const x = touch.clientX - canvasLeft
      const y = touch.clientY - canvasTop

      const node = nodesRef.current[dragNodeIdxRef.current]
      if (node) {
        node.x = x - dragOffsetRef.current.x
        node.y = y - dragOffsetRef.current.y
        node.vx = 0
        node.vy = 0
        // 重新激活模拟
        stableRef.current = false
        render()
      }
    })
  }, [render])

  /* ---- 触控事件：touchend ---- */
  const handleTouchEnd = useCallback((e: any) => {
    if (isDraggingRef.current && dragNodeIdxRef.current >= 0) {
      // 检查是否在拖拽结束时选中节点
      const node = nodesRef.current[dragNodeIdxRef.current]
      if (node) {
        // 收集与该节点关联的关系
        const relations: string[] = []
        for (const edge of edgesRef.current) {
          const edgeNodes = nodesRef.current
          const sourceNode = edgeNodes[edge.source]
          const targetNode = edgeNodes[edge.target]
          if (edge.source === dragNodeIdxRef.current || edge.target === dragNodeIdxRef.current) {
            const otherNode = edge.source === dragNodeIdxRef.current ? targetNode : sourceNode
            relations.push(`${EDGE_LABELS[edge.type] || edge.type} → ${otherNode.name}`)
          }
        }
        setSelectedNode({ node, relations })
      }
    }
    isDraggingRef.current = false
    dragNodeIdxRef.current = -1
    // 重新运行物理模拟
    startAnimation()
  }, [startAnimation])

  /* ---- 点击节点弹窗后的跳转 ---- */
  const goToCardDetail = useCallback((id: string) => {
    // 节点ID格式如 'person:123'，提取数字部分
    const parts = id.split(':')
    const realId = parts[parts.length - 1] || id
    Taro.navigateTo({ url: `/pages/card-detail/index?id=${realId}` })
  }, [])

  /* ---- 筛选切换 ---- */
  const handleFilterChange = useCallback((key: string) => {
    setFilterType(key)
  }, [])

  /* ---- 点击节点弹窗关闭 ---- */
  const closeDetail = useCallback(() => {
    setSelectedNode(null)
  }, [])

  /* ---- 重试 ---- */
  const handleRetry = useCallback(() => {
    initCanvas()
  }, [initCanvas])

  /* ---- 分享人脉图 ---- */
  Taro.useShareAppMessage(() => {
    incrementShareCount()
    return {
      title: '我的人脉网络图谱 - AI数字名片',
      path: '/pages/network/index',
    }
  })

  /* ---- 初始化 ---- */
  useEffect(() => {
    // 延迟一帧确保DOM就绪
    setTimeout(() => {
      initCanvas()
    }, 100)

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* ---- 数据就绪后启动动画 ---- */
  useEffect(() => {
    if (status === 'ready' && nodesRef.current.length > 0) {
      startAnimation()
    }
  }, [status, startAnimation])

  /* ---- 筛选变化时重新初始化和渲染图谱 ---- */
  useEffect(() => {
    if (status !== 'ready') return
    const raw = rawDataRef.current
    if (!raw || raw.nodes.length === 0) return
    const filtered = filterGraphData(raw, filterType)
    initGraph(filtered)
    // 下一帧启动模拟
    setTimeout(() => {
      startAnimation()
    }, 50)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterType])

  /* ================================================================ */
  /*  渲染                                                              */
  /* ================================================================ */

  /* --- Loading --- */
  if (status === 'loading') {
    return (
      <View className='network'>
        <View className='network__status-overlay'>
          <Text className='network__loading-icon'>⚡</Text>
          <Text className='network__loading-text'>正在构建人脉网络...</Text>
        </View>
      </View>
    )
  }

  /* --- Error --- */
  if (status === 'error') {
    return (
      <View className='network'>
        <View className='network__status-overlay'>
          <Text className='network__error-icon'>😵</Text>
          <Text className='network__error-title'>加载失败</Text>
          <Text className='network__error-message'>{errorMsg || '请检查网络后重试'}</Text>
          <Button className='network__error-btn' onClick={handleRetry}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  /* --- Empty --- */
  if (status === 'empty') {
    return (
      <View className='network'>
        <View className='network__status-overlay'>
          <Text className='network__empty-icon'>🌐</Text>
          <Text className='network__empty-title'>暂无数据</Text>
          <Text className='network__empty-desc'>
            创建名片并建立连接后，这里将展示您的人脉网络
          </Text>
        </View>
      </View>
    )
  }

  /* ================================================================ */
  /*  主页面                                                            */
  /* ================================================================ */

  return (
    <View className='network'>
      {/* Canvas（全屏底层） */}
      <View className='network__canvas-wrapper'>
        <Canvas
          id={CANVAS_ID}
          className='network__canvas'
          type='2d'
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          onTouchCancel={handleTouchEnd}
        />
      </View>

      {/* 顶部导航 */}
      <View className='network__header'>
        <View className='network__title-row'>
          <Text className='network__title'>人脉网络</Text>
          <View className='network__stats'>
            <View className='network__stat-item'>
              <Text className='network__stat-value'>{connCount}</Text>
              <Text className='network__stat-label'>连接人</Text>
            </View>
            <View className='network__stat-item'>
              <Text className='network__stat-value'>{relationCount}</Text>
              <Text className='network__stat-label'>种关系</Text>
            </View>
          </View>
        </View>
      </View>

      {/* 洞察面板（轻量信息卡片） */}
      {insights && (
        <View className='network__insights'>
          <View className='network__insights-item'>
            <Text className='network__insights-value'>{insights.connection_count ?? connCount}</Text>
            <Text className='network__insights-label'>连接数</Text>
          </View>
          <View className='network__insights-divider' />
          <View className='network__insights-item'>
            <Text className='network__insights-value'>{insights.industry_count ?? '-'}</Text>
            <Text className='network__insights-label'>覆盖行业</Text>
          </View>
          <View className='network__insights-divider' />
          <View className='network__insights-item'>
            <Text className='network__insights-value'>
              {insights.influence_score != null ? insights.influence_score.toFixed(1) : '-'}
            </Text>
            <Text className='network__insights-label'>影响力</Text>
          </View>
          <View className='network__insights-divider' />
          <View className='network__insights-item'>
            <Text className='network__insights-value'>
              {insights.centrality_score != null ? (insights.centrality_score * 100).toFixed(0) + '%' : '-'}
            </Text>
            <Text className='network__insights-label'>中心度</Text>
          </View>
        </View>
      )}

      {/* 筛选按钮（横滑） */}
      <View className='network__filters'>
        {FILTER_ITEMS.map((item) => (
          <View
            key={item.key}
            className={`network__filter-btn${filterType === item.key ? ' network__filter-btn--active' : ''}`}
            onClick={() => handleFilterChange(item.key)}
          >
            <Text className='network__filter-btn-text'>{item.label}</Text>
          </View>
        ))}
      </View>

      {/* 底部图例 */}
      <View className='network__legend'>
        {LEGEND_ITEMS.map((item) => (
          <View key={item.type} className='network__legend-item'>
            <View
              className='network__legend-dot'
              style={{ backgroundColor: NODE_COLORS[item.type] }}
            />
            <Text className='network__legend-label'>{item.label}</Text>
          </View>
        ))}

        {/* 统计折叠按钮 */}
        <View
          className='network__stats-toggle'
          onClick={() => setShowStats((v) => !v)}
        >
          <Text className='network__stats-toggle-icon'>{showStats ? '▼' : '▲'}</Text>
        </View>
      </View>

      {/* 统计小面板（折叠） */}
      {showStats && (
        <View className='network__stats-panel'>
          <View className='network__stats-panel-row'>
            <Text className='network__stats-panel-label'>连接人数</Text>
            <Text className='network__stats-panel-value'>{connCount}</Text>
          </View>
          <View className='network__stats-panel-row'>
            <Text className='network__stats-panel-label'>行业数</Text>
            <Text className='network__stats-panel-value'>
              {insights?.industry_count ?? (() => {
                const industries = new Set(
                  nodesRef.current
                    .filter((n) => n.type === 'industry')
                    .map((n) => n.name),
                )
                return industries.size || '-'
              })()}
            </Text>
          </View>
          <View className='network__stats-panel-row'>
            <Text className='network__stats-panel-label'>关系总数</Text>
            <Text className='network__stats-panel-value'>{edgesRef.current.length}</Text>
          </View>
          <View className='network__stats-panel-row'>
            <Text className='network__stats-panel-label'>影响力评分</Text>
            <Text className='network__stats-panel-value'>
              {insights?.influence_score != null ? insights.influence_score.toFixed(1) : '-'}
            </Text>
          </View>
        </View>
      )}

      {/* 分享人脉图按钮 */}
      <View
        className='network__share-btn'
        onClick={() => {
          Taro.showShareMenu({
            withShareTicket: true,
          })
        }}
      >
        <Text className='network__share-btn-icon'>📤</Text>
        <Text className='network__share-btn-text'>分享人脉图</Text>
        <Text className='network__share-btn-sub'>{getShareLimitText()}</Text>
      </View>

      {/* 节点详情弹窗 */}
      {selectedNode && (
        <View className='network__detail-overlay' onClick={closeDetail}>
          <View
            className='network__detail-panel'
            onClick={(e) => { e.stopPropagation() }}
          >
            <View className='network__detail-handle' />
            <View className='network__detail-header'>
              <Text className='network__detail-name'>{selectedNode.node.name}</Text>
              <Text
                className={[
                  'network__detail-type-tag',
                  `network__detail-type-tag--${selectedNode.node.type}`,
                ].join(' ')}
              >
                {selectedNode.node.type === 'center'
                  ? '我'
                  : selectedNode.node.type === 'person'
                    ? '人脉'
                    : selectedNode.node.type === 'company'
                      ? '公司'
                      : selectedNode.node.type === 'industry'
                        ? '行业'
                        : '标签'}
              </Text>
            </View>

            <View className='network__detail-body'>
              {/* 公司信息 */}
              {selectedNode.node.company && (
                <View className='network__detail-row'>
                  <Text className='network__detail-row-label'>公司</Text>
                  <Text className='network__detail-row-value'>
                    {selectedNode.node.company}
                  </Text>
                </View>
              )}

              {/* 匹配度 */}
              {selectedNode.node.match_score !== undefined && (
                <View className='network__detail-row'>
                  <Text className='network__detail-row-label'>匹配度</Text>
                  <Text className='network__detail-row-value'>
                    {Math.round(selectedNode.node.match_score * 100)}%
                  </Text>
                </View>
              )}

              {/* 连接数 */}
              <View className='network__detail-row'>
                <Text className='network__detail-row-label'>连接数</Text>
                <Text className='network__detail-row-value'>
                  {selectedNode.node.connectionCount}
                </Text>
              </View>

              {/* 关系类型 */}
              {selectedNode.relations.length > 0 && (
                <View className='network__detail-row'>
                  <Text className='network__detail-row-label'>关系</Text>
                  <View className='network__detail-relation-list'>
                    {selectedNode.relations.map((r, i) => (
                      <Text key={i} className='network__detail-relation-tag'>
                        {r}
                      </Text>
                    ))}
                  </View>
                </View>
              )}
            </View>

            <View className='network__detail-actions'>
              {selectedNode.node.type === 'person' && (
                <Button
                  className='network__detail-btn network__detail-btn--primary'
                  onClick={() => goToCardDetail(selectedNode.node.id)}
                >
                  查看名片
                </Button>
              )}
              <Button
                className='network__detail-btn network__detail-btn--close'
                onClick={closeDetail}
              >
                关闭
              </Button>
            </View>
          </View>
        </View>
      )}
    </View>
  )
}

export default Network
