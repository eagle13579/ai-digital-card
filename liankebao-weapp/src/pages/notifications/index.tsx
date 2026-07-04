import { FC, useState, useEffect, useCallback, useRef } from 'react'
import { View, Text, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { notificationApi } from '../../api/digitalBrochure'
import './index.scss'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

type PageStatus = 'loading' | 'ready' | 'error' | 'empty'

type TabKey = 'all' | 'unread' | 'system' | 'transaction'

interface NotificationItem {
  id: string
  type: 'system' | 'transaction' | 'social' | 'marketing'
  title: string
  content: string
  created_at: string
  is_read: boolean
  icon?: string
}

/* ========================================================================== */
/*  常量                                                                       */
/* ========================================================================== */

const TABS: { key: TabKey; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'unread', label: '未读' },
  { key: 'system', label: '系统' },
  { key: 'transaction', label: '交易' },
]

const TYPE_ICONS: Record<string, string> = {
  system: '🔔',
  transaction: '💰',
  social: '🤝',
  marketing: '📢',
}

const PAGE_SIZE = 20

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Notifications: FC = () => {
  /* ---- 状态 ---- */
  const [status, setStatus] = useState<PageStatus>('loading')
  const [errorMsg, setErrorMsg] = useState('')
  const [activeTab, setActiveTab] = useState<TabKey>('all')
  const [list, setList] = useState<NotificationItem[]>([])
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const loadingRef = useRef(false)

  /* ---- 构建请求参数 ---- */
  const buildParams = useCallback(
    (pageNum: number) => {
      const params: any = { page: pageNum, page_size: PAGE_SIZE }
      if (activeTab === 'unread') {
        params.unread_only = true
      }
      return params
    },
    [activeTab],
  )

  /* ---- 加载数据 ---- */
  const loadList = useCallback(
    async (isRefresh = false) => {
      if (loadingRef.current) return
      loadingRef.current = true

      try {
        if (isRefresh) {
          setStatus('loading')
          setErrorMsg('')
          setPage(1)
          setHasMore(true)
        }

        const currentPage = isRefresh ? 1 : page
        const res = await notificationApi.getList(buildParams(currentPage))

        if (res.code === 200 || res.code === 0) {
          const data = (res.data as any) ?? {}
          const items: NotificationItem[] = data.list ?? []
          const total = data.total ?? 0

          if (isRefresh) {
            setList(items)
          } else {
            setList((prev) => [...prev, ...items])
          }

          setHasMore(list.length + items.length < total)
          setPage(currentPage + 1)

          if (isRefresh && items.length === 0) {
            setStatus('empty')
          } else {
            setStatus('ready')
          }
        } else {
          if (isRefresh) {
            setErrorMsg(res.message || '加载失败')
            setStatus('error')
          } else {
            Taro.showToast({ title: res.message || '加载更多失败', icon: 'none' })
          }
        }
      } catch (e: any) {
        if (isRefresh) {
          setErrorMsg(e.message || '网络异常')
          setStatus('error')
        } else {
          Taro.showToast({ title: e.message || '加载更多失败', icon: 'none' })
        }
      } finally {
        loadingRef.current = false
        setLoadingMore(false)
      }
    },
    [page, activeTab, buildParams, list.length],
  )

  /* ---- 初始化 & 切换 Tab ---- */
  useEffect(() => {
    setList([])
    setPage(1)
    setHasMore(true)
    setStatus('loading')
    // 使用延迟执行，让状态更新完成
    const timer = setTimeout(() => {
      loadList(true)
    }, 0)
    return () => clearTimeout(timer)
    // 故意保留依赖，确保 Tab 切换时重新加载
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  /* ---- 加载更多 ---- */
  const handleLoadMore = useCallback(() => {
    if (loadingMore || !hasMore || loadingRef.current) return
    setLoadingMore(true)
    loadList(false)
  }, [loadingMore, hasMore, loadList])

  /* ---- 标记已读 ---- */
  const handleMarkRead = useCallback(
    async (notificationId: string) => {
      try {
        const res = await notificationApi.markRead(notificationId)
        if (res.code === 200 || res.code === 0) {
          setList((prev) =>
            prev.map((item) =>
              item.id === notificationId ? { ...item, is_read: true } : item,
            ),
          )
        }
      } catch {
        // 静默
      }
    },
    [],
  )

  /* ---- 全部已读 ---- */
  const handleMarkAllRead = useCallback(async () => {
    try {
      const unreadItems = list.filter((item) => !item.is_read)
      if (unreadItems.length === 0) {
        Taro.showToast({ title: '没有未读消息', icon: 'none' })
        return
      }

      Taro.showLoading({ title: '标记中...' })
      // 逐条标记
      for (const item of unreadItems) {
        await notificationApi.markRead(item.id)
      }
      Taro.hideLoading()

      setList((prev) => prev.map((item) => ({ ...item, is_read: true })))
      Taro.showToast({ title: '已全部标记已读', icon: 'success' })
    } catch {
      Taro.hideLoading()
      Taro.showToast({ title: '操作失败', icon: 'none' })
    }
  }, [list])

  /* ---- 格式化时间 ---- */
  const formatTime = useCallback((dateStr: string) => {
    try {
      const date = new Date(dateStr)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMin = Math.floor(diffMs / 60000)
      const diffHour = Math.floor(diffMs / 3600000)
      const diffDay = Math.floor(diffMs / 86400000)

      if (diffMin < 1) return '刚刚'
      if (diffMin < 60) return `${diffMin}分钟前`
      if (diffHour < 24) return `${diffHour}小时前`
      if (diffDay < 7) return `${diffDay}天前`

      const y = date.getFullYear()
      const m = String(date.getMonth() + 1).padStart(2, '0')
      const d = String(date.getDate()).padStart(2, '0')
      return `${y}-${m}-${d}`
    } catch {
      return dateStr
    }
  }, [])

  /* ---- 下拉刷新 ---- */
  const handleRefresh = useCallback(() => {
    setList([])
    setPage(1)
    setHasMore(true)
    loadList(true)
  }, [loadList])

  /* ================================================================ */
  /*  渲染：各状态                                                      */
  /* ================================================================ */

  if (status === 'loading') {
    return (
      <View className='notifications'>
        <View className='notifications__skeleton'>
          {[1, 2, 3, 4, 5].map((i) => (
            <View key={i} className='notifications__skeleton-item'>
              <View className='notifications__skeleton-icon' />
              <View className='notifications__skeleton-content'>
                <View className='notifications__skeleton-title' />
                <View className='notifications__skeleton-desc' />
              </View>
            </View>
          ))}
        </View>
      </View>
    )
  }

  if (status === 'error') {
    return (
      <View className='notifications'>
        <View className='notifications__error'>
          <Text className='notifications__error-icon'>😵</Text>
          <Text className='notifications__error-title'>加载失败</Text>
          <Text className='notifications__error-message'>{errorMsg || '请检查网络后重试'}</Text>
          <Button className='notifications__error-btn' onClick={handleRefresh}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  if (status === 'empty') {
    return (
      <View className='notifications'>
        {/* Tab bar still visible */}
        <View className='notifications__tabs'>
          {TABS.map((tab) => (
            <View
              key={tab.key}
              className={`notifications__tab ${activeTab === tab.key ? 'notifications__tab--active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              <Text className='notifications__tab-text'>{tab.label}</Text>
              {activeTab === tab.key && <View className='notifications__tab-indicator' />}
            </View>
          ))}
        </View>

        <View className='notifications__empty'>
          <Text className='notifications__empty-icon'>📭</Text>
          <Text className='notifications__empty-text'>暂无消息</Text>
        </View>
      </View>
    )
  }

  const unreadCount = list.filter((item) => !item.is_read).length

  return (
    <View className='notifications'>
      {/* ================ 顶部操作栏 ================ */}
      <View className='notifications__header'>
        <Text className='notifications__header-title'>消息通知</Text>
        {unreadCount > 0 && (
          <View className='notifications__header-actions' onClick={handleMarkAllRead}>
            <Text className='notifications__header-action-text'>全部已读</Text>
          </View>
        )}
      </View>

      {/* ================ Tab 栏 ================ */}
      <View className='notifications__tabs'>
        {TABS.map((tab) => {
          const tabUnread =
            tab.key === 'all'
              ? unreadCount
              : tab.key === 'unread'
              ? unreadCount
              : list.filter((item) => !item.is_read && item.type === tab.key).length

          return (
            <View
              key={tab.key}
              className={`notifications__tab ${activeTab === tab.key ? 'notifications__tab--active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              <Text className='notifications__tab-text'>{tab.label}</Text>
              {tabUnread > 0 && (
                <View className='notifications__tab-badge'>
                  <Text className='notifications__tab-badge-text'>
                    {tabUnread > 99 ? '99+' : tabUnread}
                  </Text>
                </View>
              )}
              {activeTab === tab.key && <View className='notifications__tab-indicator' />}
            </View>
          )
        })}
      </View>

      {/* ================ 消息列表 ================ */}
      <ScrollView
        className='notifications__scroll'
        scrollY
        enhanced
        showScrollbar={false}
        lowerThreshold={100}
        onScrollToLower={handleLoadMore}
      >
        {list.map((item) => {
          const icon = item.icon || TYPE_ICONS[item.type] || '🔔'
          const isTabFiltered =
            activeTab === 'system'
              ? item.type === 'system'
              : activeTab === 'transaction'
              ? item.type === 'transaction'
              : true

          if (!isTabFiltered && activeTab !== 'all' && activeTab !== 'unread') return null
          if (activeTab === 'unread' && item.is_read) return null

          return (
            <View
              key={item.id}
              className={`notifications__item ${!item.is_read ? 'notifications__item--unread' : ''}`}
              onClick={() => handleMarkRead(item.id)}
            >
              <View className='notifications__item-icon-wrap'>
                <Text className='notifications__item-icon'>{icon}</Text>
                {!item.is_read && <View className='notifications__item-dot' />}
              </View>
              <View className='notifications__item-content'>
                <View className='notifications__item-top'>
                  <Text className='notifications__item-title'>{item.title}</Text>
                  <Text className='notifications__item-time'>{formatTime(item.created_at)}</Text>
                </View>
                <Text className='notifications__item-desc' numberOfLines={2}>
                  {item.content}
                </Text>
              </View>
            </View>
          )
        })}

        {/* 加载更多指示器 */}
        {loadingMore && (
          <View className='notifications__loading'>
            <Text className='notifications__loading-text'>加载中...</Text>
          </View>
        )}
        {!hasMore && list.length > 0 && (
          <View className='notifications__no-more'>
            <Text className='notifications__no-more-text'>— 没有更多了 —</Text>
          </View>
        )}

        <View className='notifications__bottom-spacer' />
      </ScrollView>
    </View>
  )
}

export default Notifications
