import { FC, useState, useEffect, useCallback } from 'react'
import { View, Text, Image, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import userApi, { UserInfo } from '../../api/user'
import cardApi from '../../api/card'
import { growthApi, notificationApi } from '../../api/digitalBrochure'
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
  { key: 'orders', icon: '📋', title: '我的订单', url: '/pages/orders/index' },
  { key: 'vip', icon: '👑', title: '会员中心', url: '/pages/vip/index' },
  { key: 'notifications', icon: '🔔', title: '消息通知', url: '/pages/notifications/index' },
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

  /* ---- 初始化 ---- */
  useEffect(() => {
    initPage()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const initPage = async () => {
    setStatus('loading')
    setErrorMsg('')
    try {
      await Promise.all([loadUser(), loadMetrics(), loadUnread()])
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
