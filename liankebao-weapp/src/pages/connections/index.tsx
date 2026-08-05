/**
 * 社交关系管理 — 我的连接 + 待审核请求
 *
 * API:
 *   GET  /api/business-card/connections       — 好友列表
 *   GET  /api/business-card/connections/pending — 待审核请求
 *   PUT  /api/business-card/connections/:id/review — 审核请求
 *   POST /api/business-card/connections/request   — 发起建联
 */

import { FC, useState, useEffect, useCallback } from 'react'
import { View, Text, Image, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import connectionApi, { ConnectionUser, PendingRequest } from '../../api/connection'
import './index.scss'

/* ========================================================================== */
/*  常量                                                                       */
/* ========================================================================== */

const TAB_KEYS = ['connections', 'pending'] as const
type TabKey = (typeof TAB_KEYS)[number]

const TAB_LABELS: Record<TabKey, string> = {
  connections: '我的连接',
  pending: '待审核',
}

type PageStatus = 'loading' | 'ready' | 'error'

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Connections: FC = () => {
  /* ---- 全局状态 ---- */
  const [activeTab, setActiveTab] = useState<TabKey>('connections')
  const [status, setStatus] = useState<PageStatus>('loading')
  const [errorMsg, setErrorMsg] = useState('')

  /* ---- 我的连接 ---- */
  const [connections, setConnections] = useState<ConnectionUser[]>([])
  const [connectionsLoaded, setConnectionsLoaded] = useState(false)

  /* ---- 待审核 ---- */
  const [pendingList, setPendingList] = useState<PendingRequest[]>([])
  const [pendingLoaded, setPendingLoaded] = useState(false)

  /* ================================================================ */
  /*  数据加载                                                          */
  /* ================================================================ */

  /** 加载已approved的好友列表 */
  const loadConnections = useCallback(async () => {
    try {
      const res = await connectionApi.list('approved')
      if (res.code === 200 || res.code === 0) {
        const list = res.data || []
        setConnections(Array.isArray(list) ? (list as ConnectionUser[]) : [])
      } else {
        setConnections([])
      }
    } catch {
      setConnections([])
    } finally {
      setConnectionsLoaded(true)
    }
  }, [])

  /** 加载待审核请求 */
  const loadPending = useCallback(async () => {
    try {
      const res = await connectionApi.listPending()
      if (res.code === 200 || res.code === 0) {
        const list = res.data || []
        setPendingList(Array.isArray(list) ? (list as PendingRequest[]) : [])
      } else {
        setPendingList([])
      }
    } catch {
      setPendingList([])
    } finally {
      setPendingLoaded(true)
    }
  }, [])

  /** 加载所有数据 */
  const loadAll = useCallback(async () => {
    setStatus('loading')
    setErrorMsg('')
    setConnectionsLoaded(false)
    setPendingLoaded(false)
    try {
      await Promise.all([loadConnections(), loadPending()])
      setStatus('ready')
    } catch {
      setErrorMsg('加载失败，请检查网络后重试')
      setStatus('error')
    }
  }, [loadConnections, loadPending])

  useEffect(() => {
    loadAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* ================================================================ */
  /*  操作                                                              */
  /* ================================================================ */

  /** 审核请求 — 批准/拒绝 */
  const handleReview = useCallback(
    async (connectionId: number, approved: boolean) => {
      Taro.showLoading({ title: approved ? '正在批准...' : '正在拒绝...' })
      try {
        const res = await connectionApi.review(connectionId, approved)
        Taro.hideLoading()
        if (res.code === 200 || res.code === 0) {
          Taro.showToast({
            title: approved ? '已建立连接' : '已拒绝',
            icon: 'success',
          })
          // 刷新待审核列表
          loadPending()
          // 如果批准了，也刷新连接列表
          if (approved) loadConnections()
        } else {
          Taro.showToast({ title: res.message || '操作失败', icon: 'none' })
        }
      } catch (e: any) {
        Taro.hideLoading()
        Taro.showToast({ title: e.message || '操作失败', icon: 'none' })
      }
    },
    [loadConnections, loadPending],
  )

  /** 点击连接 → 跳转名片详情 */
  const goToCardDetail = useCallback((connection: ConnectionUser) => {
    Taro.navigateTo({
      url: `/pages/index/index?userId=${connection.id}`,
    })
  }, [])

  /** 点击待审核请求 → 查看对方名片 */
  const goToUserDetail = useCallback((request: PendingRequest) => {
    Taro.navigateTo({
      url: `/pages/index/index?userId=${request.user_id}`,
    })
  }, [])

  /** 跳转资源平台 */
  const goToSupplyDemand = useCallback(() => {
    Taro.switchTab({ url: '/pages/index/index' })
  }, [])

  /* ================================================================ */
  /*  渲染 — 页头                                                       */
  /* ================================================================ */

  const renderHeader = () => (
    <View className='connections__header'>
      <View className='connections__header-title'>
        <Text>社交关系</Text>
      </View>
      <View className='connections__tabs'>
        {TAB_KEYS.map((key) => {
          const isActive = activeTab === key
          const badge =
            key === 'pending' && pendingList.length > 0 ? pendingList.length : undefined
          return (
            <View
              key={key}
              className={`connections__tab${isActive ? ' connections__tab--active' : ''}`}
              onClick={() => setActiveTab(key)}
            >
              <Text className='connections__tab-label'>{TAB_LABELS[key]}</Text>
              {badge !== undefined && (
                <View className='connections__tab-badge'>
                  <Text className='connections__tab-badge-text'>
                    {badge > 99 ? '99+' : badge}
                  </Text>
                </View>
              )}
              {isActive && <View className='connections__tab-indicator' />}
            </View>
          )
        })}
      </View>
    </View>
  )

  /* ================================================================ */
  /*  渲染 — 骨架屏                                                     */
  /* ================================================================ */

  if (status === 'loading') {
    return (
      <View className='connections'>
        {renderHeader()}
        <View className='connections__skeleton'>
          {[1, 2, 3, 4].map((i) => (
            <View key={i} className='connections__skeleton-item'>
              <View className='connections__skeleton-avatar' />
              <View className='connections__skeleton-info'>
                <View className='connections__skeleton-line connections__skeleton-line--name' />
                <View className='connections__skeleton-line connections__skeleton-line--company' />
              </View>
            </View>
          ))}
        </View>
      </View>
    )
  }

  /* ================================================================ */
  /*  渲染 — 错误状态                                                   */
  /* ================================================================ */

  if (status === 'error') {
    return (
      <View className='connections'>
        {renderHeader()}
        <View className='connections__error'>
          <Text className='connections__error-icon'>😵</Text>
          <Text className='connections__error-title'>加载失败</Text>
          <Text className='connections__error-msg'>{errorMsg || '请检查网络后重试'}</Text>
          <Button className='connections__error-btn' onClick={loadAll}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  /* ================================================================ */
  /*  渲染 — 连接列表                                                   */
  /* ================================================================ */

  const renderConnections = () => {
    if (connections.length === 0 && connectionsLoaded) {
      return (
        <View className='connections__empty'>
          <Text className='connections__empty-icon'>🤝</Text>
          <Text className='connections__empty-title'>暂无连接</Text>
          <Text className='connections__empty-desc'>
            去资源平台找人交换名片吧
          </Text>
          <Button className='connections__empty-btn' onClick={goToSupplyDemand}>
            前往资源平台
          </Button>
        </View>
      )
    }

    return (
      <View className='connections__list'>
        {connections.map((item) => (
          <View
            key={item.connection_id}
            className='connections__card'
            hoverClass='connections__card--active'
            onClick={() => goToCardDetail(item)}
          >
            <Image
              className='connections__avatar'
              src={item.avatar || ''}
              mode='aspectFill'
            />
            <View className='connections__card-body'>
              <View className='connections__card-top'>
                <Text className='connections__card-name' numberOfLines={1}>
                  {item.name}
                </Text>
                {item.label && (
                  <View className='connections__card-label'>
                    <Text className='connections__card-label-text'>{item.label}</Text>
                  </View>
                )}
              </View>
              <Text className='connections__card-meta' numberOfLines={1}>
                {[item.company, item.title].filter(Boolean).join(' · ')}
              </Text>
              <Text className='connections__card-time'>
                建立于 {item.created_at ? item.created_at.slice(0, 10) : ''}
              </Text>
            </View>
            <Text className='connections__card-arrow'>›</Text>
          </View>
        ))}
      </View>
    )
  }

  /* ================================================================ */
  /*  渲染 — 待审核列表                                                 */
  /* ================================================================ */

  const renderPending = () => {
    if (pendingList.length === 0 && pendingLoaded) {
      return (
        <View className='connections__empty'>
          <Text className='connections__empty-icon'>📬</Text>
          <Text className='connections__empty-title'>暂无待审核请求</Text>
          <Text className='connections__empty-desc'>
            当有人向您发起建联时，会显示在这里
          </Text>
        </View>
      )
    }

    return (
      <View className='connections__list'>
        {pendingList.map((item) => (
          <View
            key={item.connection_id}
            className='connections__card'
            hoverClass='connections__card--active'
            onClick={() => goToUserDetail(item)}
          >
            <Image
              className='connections__avatar'
              src={item.avatar || ''}
              mode='aspectFill'
            />
            <View className='connections__card-body'>
              <View className='connections__card-top'>
                <Text className='connections__card-name' numberOfLines={1}>
                  {item.name}
                </Text>
                {item.source && (
                  <View className='connections__card-source'>
                    <Text className='connections__card-source-text'>
                      来自{item.source === 'platform' ? '资源平台' : item.source}
                    </Text>
                  </View>
                )}
              </View>
              <Text className='connections__card-meta' numberOfLines={1}>
                {[item.company, item.title].filter(Boolean).join(' · ')}
              </Text>
              <View className='connections__card-actions'>
                <Button
                  className='connections__action-btn connections__action-btn--approve'
                  onClick={(e) => {
                    e.stopPropagation()
                    handleReview(item.connection_id, true)
                  }}
                >
                  批准
                </Button>
                <Button
                  className='connections__action-btn connections__action-btn--reject'
                  onClick={(e) => {
                    e.stopPropagation()
                    handleReview(item.connection_id, false)
                  }}
                >
                  拒绝
                </Button>
              </View>
            </View>
          </View>
        ))}
      </View>
    )
  }

  /* ================================================================ */
  /*  主渲染                                                            */
  /* ================================================================ */

  return (
    <View className='connections'>
      {renderHeader()}

      <ScrollView
        className='connections__scroll'
        scrollY
        enhanced
        showScrollbar={false}
      >
        {activeTab === 'connections' ? renderConnections() : renderPending()}
        <View className='connections__bottom-spacer' />
      </ScrollView>
    </View>
  )
}

export default Connections
