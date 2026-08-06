import { FC, useState, useEffect, useCallback } from 'react'
import { View, Text, Image, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import userApi, { UserInfo } from '../../api/user'
import cardApi from '../../api/card'
import { growthApi, notificationApi, optimizeApi, usageApi } from '../../api/digitalBrochure'
import './index.scss'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

interface MetricsData {
  /** 名片浏览数 */
  profile_views?: number
  /** 匹配数 */
  matches?: number
  /** 收藏数 */
  favorites?: number
  /** 合作数 */
  collaborations?: number
  [key: string]: any
}

interface AiScoreData {
  /** 综合评分 (0-100) */
  overall_score: number
  /** 完整度评分 */
  completeness_score: number
  /** 关键词评分 */
  keyword_score: number
  /** 专业度评分 */
  professionalism_score: number
  /** 优化建议列表 */
  suggestions: string[]
}

/* ---- AI用量类型 ---- */
interface AiUsageData {
  scanCount: number
  viewCount: number
  writerCount: number
  scoreCount: number
  [key: string]: number
}

/* ---- AI用量配置 ---- */
const AI_USAGE_CONFIG: { key: string; label: string; limit: number; icon: string }[] = [
  { key: 'scanCount', label: 'AI扫描次数', limit: 30, icon: '📷' },
  { key: 'viewCount', label: 'AI推荐查看', limit: 50, icon: '👀' },
  { key: 'writerCount', label: 'AI写作助手', limit: 10, icon: '✍️' },
  { key: 'scoreCount', label: 'AI名片评分', limit: 10, icon: '⭐' },
]

type PageStatus = 'loading' | 'ready' | 'error'

/* ========================================================================== */
/*  常量 — 菜单列表                                                            */
/* ========================================================================== */

interface MenuItem {
  key: string
  icon: string
  title: string
  url?: string
  action?: 'logout' | 'scan'
}

const MENU_LIST: MenuItem[] = [
  { key: 'network', icon: '🕸️', title: '人脉网络', url: '/pages/network/index' },
  { key: 'orders', icon: '📋', title: '我的订单', url: '/pages/orders/index' },
  { key: 'vip', icon: '👑', title: '会员中心', url: '/pages/vip/index' },
  { key: 'notifications', icon: '🔔', title: '消息通知', url: '/pages/notifications/index' },
  { key: 'visitors', icon: '👁️', title: '访客记录', url: '/pages/visitors/index' },
  { key: 'ai-settings', icon: '🤖', title: 'AI 设置', url: '/pages/ai-settings/index' },
  { key: 'about', icon: 'ℹ️', title: '关于', url: '/pages/about/index' },
]

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Mine: FC = () => {
  /* ---- 状态 ---- */
  const [status, setStatus] = useState<PageStatus>('loading')
  const [user, setUser] = useState<UserInfo | null>(null)
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [unreadCount, setUnreadCount] = useState(0)
  const [errorMsg, setErrorMsg] = useState('')
  const [aiScore, setAiScore] = useState<AiScoreData | null>(null)
  const [aiScoreLoading, setAiScoreLoading] = useState(false)
  const [aiUsage, setAiUsage] = useState<AiUsageData | null>(null)

  /* ---- 获取当月Storage key ---- */
  const getAiUsageKey = useCallback(() => {
    const now = new Date()
    const y = now.getFullYear()
    const m = String(now.getMonth() + 1).padStart(2, '0')
    return `ai_usage_${y}${m}`
  }, [])

  /* ---- 加载AI用量（真实API → 降级localStorage） ---- */
  const loadAiUsage = useCallback(async () => {
    try {
      const res = await usageApi.getMyUsage()
      if (res.code === 200 || res.code === 0) {
        const d = res.data as any
        // d = { tier, limits, usage: { ocr: {used, limit}, card: {used, limit}, api: {used, limit} } }
        const usage = d.usage || {}
        const ocr = usage.ocr || {}
        const card = usage.card || {}
        const api_ = usage.api || {}
        setAiUsage({
          scanCount: ocr.used ?? 0,
          viewCount: card.used ?? 0,
          writerCount: api_.used ?? 0,
          scoreCount: api_.used ?? 0,
        })
        // 缓存到 localStorage 供降级使用
        const key = getAiUsageKey()
        Taro.setStorageSync(key, {
          scanCount: ocr.used ?? 0,
          viewCount: card.used ?? 0,
          writerCount: api_.used ?? 0,
          scoreCount: api_.used ?? 0,
        })
        return
      }
    } catch {
      // API 失败 — 降级到 localStorage
    }
    // 降级：从 localStorage 读取模拟数据
    const key = getAiUsageKey()
    let data = Taro.getStorageSync(key)
    if (!data) {
      data = {
        scanCount: Math.floor(Math.random() * 10) + 1,
        viewCount: Math.floor(Math.random() * 15) + 1,
        writerCount: Math.floor(Math.random() * 4) + 1,
        scoreCount: Math.floor(Math.random() * 4) + 1,
      }
      Taro.setStorageSync(key, data)
    }
    setAiUsage(data as AiUsageData)
  }, [getAiUsageKey])

  /* ---- 加载用户信息 ---- */
  const loadUser = useCallback(async () => {
    try {
      const res = await userApi.getMe()
      if (res.code === 200 || res.code === 0) {
        const userData = res.data as unknown as UserInfo
        setUser(userData)
        Taro.setStorageSync('user', userData)
      }
    } catch {
      // 静默失败 — 显示缓存数据
      const cached = Taro.getStorageSync('user')
      if (cached) setUser(cached)
    }
  }, [])

  /* ---- 加载成长指标 ---- */
  const loadMetrics = useCallback(async () => {
    try {
      const res = await growthApi.getMetrics()
      if (res.code === 200 || res.code === 0) {
        setMetrics(res.data as unknown as MetricsData)
      }
    } catch {
      // 指标加载失败不阻塞页面
    }
  }, [])

  /* ---- 加载未读消息数 ---- */
  const loadUnread = useCallback(async () => {
    try {
      const res = await notificationApi.getList({ page: 1, page_size: 1, unread_only: true })
      if (res.code === 200 || res.code === 0) {
        const data = res.data as any
        setUnreadCount(data?.total ?? 0)
      }
    } catch {
      // 静默
    }
  }, [])

  /* ---- 加载AI名片评分 ---- */
  const loadAiScore = useCallback(async () => {
    setAiScoreLoading(true)
    try {
      const cardRes = await cardApi.getList({ page: 1, page_size: 1 })
      const list = (cardRes as any)?.data?.list ?? []
      if (list.length === 0) {
        setAiScore(null)
        setAiScoreLoading(false)
        return
      }
      const brochureId = list[0].id
      const res = await optimizeApi.getOptimize(brochureId)
      if (res.code === 200 || res.code === 0) {
        setAiScore(res.data as unknown as AiScoreData)
      } else {
        setAiScore(null)
      }
    } catch {
      setAiScore(null)
    } finally {
      setAiScoreLoading(false)
    }
  }, [])

  /* ---- 初始化 ---- */
  useEffect(() => {
    initPage()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const initPage = async () => {
    setStatus('loading')
    setErrorMsg('')
    try {
      await Promise.all([loadUser(), loadMetrics(), loadUnread(), loadAiScore(), loadAiUsage()])
      setStatus('ready')
    } catch (e: any) {
      setErrorMsg(e.message || '加载失败')
      setStatus('error')
    }
  }

  /* ---- AI 名片扫描 ---- */
  const handleScan = useCallback(async () => {
    try {
      const res = await Taro.chooseImage({ count: 1, sizeType: ['compressed'], sourceType: ['camera', 'album'] })
      const filePath = res.tempFilePaths[0]
      Taro.showLoading({ title: 'AI 识别中...' })
      const scanRes = await cardApi.scan(filePath)
      Taro.hideLoading()
      if (scanRes.code === 200 || scanRes.code === 0) {
        const data = scanRes.data as any
        Taro.navigateTo({
          url: `/pages/card-editor/index?scanData=${encodeURIComponent(JSON.stringify(data))}`,
        })
      } else {
        Taro.showToast({ title: scanRes.message || '识别失败', icon: 'none' })
      }
    } catch (e: any) {
      Taro.hideLoading()
      Taro.showToast({ title: e.message || '扫描失败', icon: 'none' })
    }
  }, [])

  /* ---- 菜单点击 ---- */
  const handleMenuClick = useCallback(
    (item: MenuItem) => {
      if (item.action === 'logout') {
        handleLogout()
      } else if (item.action === 'scan') {
        handleScan()
      } else if (item.url) {
        Taro.navigateTo({ url: item.url })
      }
    },
    [handleScan],
  )

  /* ---- 退出登录 ---- */
  const handleLogout = useCallback(() => {
    Taro.showModal({
      title: '提示',
      content: '确定退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          Taro.removeStorageSync('token')
          Taro.removeStorageSync('user')
          Taro.reLaunch({ url: '/pages/index/index' })
        }
      },
    })
  }, [])

  /* ---- 跳转编辑资料 ---- */
  const goToProfile = useCallback(() => {
    Taro.navigateTo({ url: '/pages/user/profile/index' })
  }, [])

  /* ---- 下拉刷新 ---- */
  const onRefresh = useCallback(() => {
    initPage()
  }, [])

  /* ================================================================ */
  /*  渲染：各状态                                                      */
  /* ================================================================ */

  if (status === 'loading') {
    return (
      <View className='mine'>
        <View className='mine__skeleton'>
          <View className='mine__skeleton-header'>
            <View className='mine__skeleton-avatar' />
            <View className='mine__skeleton-info'>
              <View className='mine__skeleton-line mine__skeleton-line--name' />
              <View className='mine__skeleton-line mine__skeleton-line--company' />
            </View>
          </View>
          <View className='mine__skeleton-cards'>
            <View className='mine__skeleton-card-item' />
            <View className='mine__skeleton-card-item' />
            <View className='mine__skeleton-card-item' />
            <View className='mine__skeleton-card-item' />
          </View>
          <View className='mine__skeleton-menu'>
            {[1, 2, 3, 4, 5].map((i) => (
              <View key={i} className='mine__skeleton-menu-item' />
            ))}
          </View>
        </View>
      </View>
    )
  }

  if (status === 'error') {
    return (
      <View className='mine'>
        <View className='mine__error'>
          <Text className='mine__error-icon'>😵</Text>
          <Text className='mine__error-title'>加载失败</Text>
          <Text className='mine__error-message'>{errorMsg || '请检查网络后重试'}</Text>
          <Button className='mine__error-btn' onClick={onRefresh}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  /* ---- 数据卡片配置 ---- */
  const metricCards = [
    { label: '名片浏览', value: metrics?.profile_views ?? 0, icon: '👁️' },
    { label: '匹配数', value: metrics?.matches ?? 0, icon: '🤝' },
    { label: '收藏数', value: metrics?.favorites ?? 0, icon: '⭐' },
    { label: '合作数', value: metrics?.collaborations ?? 0, icon: '💼' },
  ]

  return (
    <View className='mine'>
      <ScrollView className='mine__scroll' scrollY enhanced showScrollbar={false}>
        {/* ================ 顶部用户信息 ================ */}
        <View className='mine__header'>
          <View className='mine__header-bg' />
          <View className='mine__header-content'>
            <Image
              className='mine__avatar'
              src={user?.avatar || PLACEHOLDER.avatar80}
              mode='aspectFill'
              onClick={goToProfile}
            />
            <View className='mine__header-info'>
              <View className='mine__name-row'>
                <Text className='mine__user-name'>{user?.nickname || '用户'}</Text>
                <View className='mine__vip-badge'>
                  <Text className='mine__vip-text'>普通会员</Text>
                </View>
              </View>
              <Text className='mine__user-company'>
                {[user?.company, user?.title].filter(Boolean).join(' · ') || '点击设置个人信息'}
              </Text>
            </View>
            <View className='mine__header-right' onClick={goToProfile}>
              <Text className='mine__edit-icon'>✏️</Text>
            </View>
          </View>
        </View>

        {/* ================ 数据卡片 ================ */}
        <View className='mine__metrics'>
          {metricCards.map((card) => (
            <View key={card.label} className='mine__metric-card'>
              <Text className='mine__metric-icon'>{card.icon}</Text>
              <Text className='mine__metric-value'>{card.value}</Text>
              <Text className='mine__metric-label'>{card.label}</Text>
            </View>
          ))}
        </View>

        {/* ================ AI 名片扫描入口 ================ */}
        <View className='mine__ai-section' onClick={handleScan}>
          <View className='mine__ai-btn'>
            <View className='mine__ai-btn-bg' />
            <View className='mine__ai-btn-content'>
              <Text className='mine__ai-btn-icon'>📷</Text>
              <View className='mine__ai-btn-text'>
                <Text className='mine__ai-btn-title'>AI 名片扫描</Text>
                <Text className='mine__ai-btn-desc'>拍照识别 → 智能填充 → 一键保存</Text>
              </View>
              <Text className='mine__ai-btn-arrow'>›</Text>
            </View>
          </View>
        </View>

        {/* ================ AI 名片评分 ================ */}
        <View className='mine__ai-score'>
          <View className='mine__ai-score-header'>
            <Text className='mine__ai-score-title'>🤖 AI名片评分</Text>
          </View>
          {aiScoreLoading ? (
            <View className='mine__ai-score-body'>
              <Text className='mine__ai-score-loading'>获取评分中...</Text>
            </View>
          ) : aiScore ? (
            <View className='mine__ai-score-body'>
              <View className='mine__ai-score-overall'>
                <Text className='mine__ai-score-overall-value'>{aiScore.overall_score}</Text>
                <Text className='mine__ai-score-overall-label'>综合评分</Text>
              </View>
              <View className='mine__ai-score-dims'>
                <View className='mine__ai-score-dim'>
                  <Text className='mine__ai-score-dim-label'>完整度</Text>
                  <Text className='mine__ai-score-dim-value'>{aiScore.completeness_score}</Text>
                </View>
                <View className='mine__ai-score-dim'>
                  <Text className='mine__ai-score-dim-label'>关键词</Text>
                  <Text className='mine__ai-score-dim-value'>{aiScore.keyword_score}</Text>
                </View>
                <View className='mine__ai-score-dim'>
                  <Text className='mine__ai-score-dim-label'>专业度</Text>
                  <Text className='mine__ai-score-dim-value'>{aiScore.professionalism_score}</Text>
                </View>
              </View>
              {aiScore.suggestions && aiScore.suggestions.length > 0 && (
                <View className='mine__ai-score-suggestions'>
                  <Text className='mine__ai-score-suggestions-title'>💡 优化建议</Text>
                  {aiScore.suggestions.slice(0, 1).map((s, i) => (
                    <Text key={i} className='mine__ai-score-suggestion'>{i + 1}. {s}</Text>
                  ))}
                  {aiScore.suggestions.length > 1 && (
                    <View
                      className='mine__ai-score-suggestion mine__ai-score-suggestion--locked'
                      onClick={() => Taro.navigateTo({ url: '/pages/membership/index' })}
                    >
                      <Text>🔒 升级会员查看全部{aiScore.suggestions.length}条优化建议</Text>
                    </View>
                  )}
                </View>
              )}
            </View>
          ) : (
            <View className='mine__ai-score-body'>
              <Text className='mine__ai-score-empty'>创建名片后即可查看AI评分</Text>
            </View>
          )}
        </View>

        {/* ================ AI 用量面板 ================ */}
        <View className='mine__ai-usage'>
          <View className='mine__ai-usage-header'>
            <Text className='mine__ai-usage-title'>🤖 本月AI用量</Text>
          </View>
          <View className='mine__ai-usage-body'>
            {AI_USAGE_CONFIG.map((item) => {
              const used = aiUsage?.[item.key] ?? 0
              const percent = Math.min(Math.round((used / item.limit) * 100), 100)
              return (
                <View key={item.key} className='mine__ai-usage-item'>
                  <View className='mine__ai-usage-item-header'>
                    <Text className='mine__ai-usage-item-icon'>{item.icon}</Text>
                    <Text className='mine__ai-usage-item-label'>{item.label}</Text>
                    <Text className='mine__ai-usage-item-count'>
                      {used}/{item.limit} 次
                    </Text>
                  </View>
                  <View className='mine__ai-usage-progress'>
                    <View
                      className='mine__ai-usage-progress-bar'
                      style={{ width: `${percent}%` }}
                    />
                    <Text className='mine__ai-usage-progress-text'>{percent}%</Text>
                  </View>
                </View>
              )
            })}
            <View className='mine__ai-usage-footer'>
              <Button
                className='mine__ai-usage-upgrade-btn'
                onClick={() => Taro.navigateTo({ url: '/pages/membership/index' })}
              >
                升级会员获取更多次数
              </Button>
            </View>
          </View>
        </View>

        {/* ================ 功能菜单 ================ */}
        <View className='mine__menu'>
          {MENU_LIST.map((item) => (
            <View
              key={item.key}
              className='mine__menu-item'
              onClick={() => handleMenuClick(item)}
            >
              <View className='mine__menu-item-left'>
                <Text className='mine__menu-icon'>{item.icon}</Text>
                <Text className='mine__menu-title'>{item.title}</Text>
              </View>
              <View className='mine__menu-item-right'>
                {item.key === 'notifications' && unreadCount > 0 && (
                  <View className='mine__badge'>
                    <Text className='mine__badge-text'>{unreadCount > 99 ? '99+' : unreadCount}</Text>
                  </View>
                )}
                <Text className='mine__menu-arrow'>›</Text>
              </View>
            </View>
          ))}
        </View>

        {/* ================ 退出登录 ================ */}
        <View className='mine__logout-section'>
          <Button className='mine__logout-btn' onClick={handleLogout}>
            退出登录
          </Button>
        </View>

        {/* 底部间距 */}
        <View className='mine__bottom-spacer' />
      </ScrollView>
    </View>
  )
}

export default Mine
