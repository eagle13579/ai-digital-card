/**
 * 供需大厅 — AI智能匹配+推荐
 *
 * 三个Tab:
 *  1. 需求广场 — 全部供需列表 (分页)
 *  2. 我的供需 — 当前用户的供需列表 (分页)
 *  3. AI推荐  — 基于当前名片(从storage读取cardId)的混合推荐
 *
 * 状态: loading / empty / error
 * 分页: 下拉加载更多 (ScrollView onScrollToLower)
 */

import { FC, useState, useEffect, useCallback, useRef } from 'react'
import { View, Text, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import matchApi, { SupplyDemandItem } from '../../api/match'
import { sagApi } from '../../api/digitalBrochure'
import { api } from '../../api/client'
import './index.scss'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

type PageStatus = 'loading' | 'ready' | 'error' | 'empty'

type TabKey = 'square' | 'mine' | 'ai'

interface TabItem {
  key: TabKey
  label: string
}

/* ========================================================================== */
/*  常量                                                                       */
/* ========================================================================== */

const PAGE_SIZE = 10

/* ---- 每日推荐查看次数限制 ---- */
const DAILY_LIMIT = 3

const TABS: TabItem[] = [
  { key: 'square', label: '需求广场' },
  { key: 'mine', label: '我的供需' },
  { key: 'ai', label: 'AI推荐' },
]

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const SupplyDemand: FC = () => {
  /* ---- 状态 ------------------------------------------------------------- */
  const [activeTab, setActiveTab] = useState<TabKey>('square')
  const [status, setStatus] = useState<PageStatus>('loading')
  const [list, setList] = useState<SupplyDemandItem[]>([])
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const loadingRef = useRef(false)

  /* ---- 赞/踩反馈 ---- */
  const [feedbackTick, setFeedbackTick] = useState(0)

  /* ---- 每日推荐查看次数 ---- */
  const [dailyUsedCount, setDailyUsedCount] = useState<number>(() => {
    const d = new Date()
    const key = `daily_recommend_views_${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`
    return Number(Taro.getStorageSync(key) || 0)
  })
  const dailyRemaining = Math.max(0, DAILY_LIMIT - dailyUsedCount)
  const limitExceeded = dailyUsedCount >= DAILY_LIMIT

  const handleFeedback = useCallback(async (itemId: string, rating: number) => {
    try {
      await api.post(`/api/v1/recommend/${itemId}/feedback`, {
        rating,
        source: 'recommend',
      })
      const key = 'feedback_done'
      const doneList: string[] = Taro.getStorageSync(key) || []
      if (!doneList.includes(itemId)) {
        doneList.push(itemId)
        Taro.setStorageSync(key, doneList)
      }
      setFeedbackTick((t) => t + 1)
      Taro.showToast({ title: '感谢反馈，推荐将更精准', icon: 'none' })
    } catch (e: any) {
      Taro.showToast({ title: e.message || '反馈失败', icon: 'none' })
    }
  }, [])

  /* ---- 从 storage 读取 userId / cardId -------------------------------- */
  const getStorage = useCallback(() => {
    const userId = Taro.getStorageSync('userId') || ''
    const cardId = Taro.getStorageSync('cardId') || ''
    return { userId, cardId }
  }, [])

  /* ---- 获取数据 (根据 activeTab) ---------------------------------------- */
  const fetchData = useCallback(
    async (pageNum: number, append = false) => {
      const { userId, cardId } = getStorage()

      try {
        if (activeTab === 'ai') {
          /* -- AI推荐：混合推荐，不分页 -- */
          if (!cardId) {
            setStatus('empty')
            setList([])
            return
          }
          const res = await matchApi.getHybridRecommend(cardId)
          const raw = (res.data as any) ?? []
          const items: SupplyDemandItem[] = Array.isArray(raw)
            ? raw.map((item: any) => ({
                id: item.id || item.card_id || '',
                title: item.name || item.title || '未知',
                company: item.company || '',
                industry: item.industry || '',
                match_score: item.match_score != null ? Math.round(item.match_score * 100) : 0,
                publish_time: item.publish_time || item.created_at || '',
                description: item.description || item.match_reason || '',
                contact: item.contact || '',
                match_reason: item.match_reason || '',
              }))
            : []
          setList(items)
          setHasMore(false)
          setStatus(items.length > 0 ? 'ready' : 'empty')

          // SAG: 对缺少推荐理由的项调用SAG管道生成补充推荐解释
          if (items.length > 0) {
            const itemsToExplain = items.filter(item => !item.match_reason)
            if (itemsToExplain.length > 0) {
              ;(async () => {
                const results = await Promise.allSettled(
                  itemsToExplain.map(item =>
                    sagApi.analyze({
                      mode: 'explain_recommend',
                      content: JSON.stringify({ title: item.title, company: item.company, industry: item.industry }),
                      depth: 'fast' as any,
                    }).then(res => ({ id: item.id, conclusion: (res as any).data?.conclusion || '' }))
                  )
                )
                const updates: Record<string, string> = {}
                results.forEach(r => {
                  if (r.status === 'fulfilled' && r.value.conclusion) {
                    updates[r.value.id] = r.value.conclusion
                  }
                })
                if (Object.keys(updates).length > 0) {
                  setList(prev => prev.map(item =>
                    updates[item.id] ? { ...item, match_reason: updates[item.id] } : item
                  ))
                }
              })()
            }
          }
        } else {
          /* -- 供需列表 (需求广场 / 我的供需) -- */
          const params: any = { page: pageNum, page_size: PAGE_SIZE }
          if (activeTab === 'mine' && userId) {
            params.user_id = userId
          }
          const res = await matchApi.getMatches(params)
          const data = res.data as any
          const rawList: any[] = data?.list ?? data ?? []
          const total = data?.total ?? rawList.length

          const items: SupplyDemandItem[] = rawList.map((item: any) => ({
            id: item.id || '',
            title: item.title || item.name || '未命名',
            company: item.company || '',
            industry: item.industry || '',
            match_score: item.match_score != null ? Math.round(item.match_score * 100) : 0,
            publish_time: item.publish_time || item.created_at || '',
            description: item.description || '',
            contact: item.contact || '',
            user_id: item.user_id || '',
            purpose: item.purpose || '',
          }))

          if (append) {
            setList((prev) => [...prev, ...items])
          } else {
            setList(items)
          }

          const loadedCount = append ? list.length + items.length : items.length
          setHasMore(loadedCount < total)
          setStatus(items.length > 0 || loadedCount > 0 ? 'ready' : 'empty')
        }
      } catch (e: any) {
        const msg = e.message || '加载失败'
        setErrorMsg(msg)
        setStatus('error')
      }
    },
    [activeTab, getStorage, list.length],
  )

  /* ---- 初始加载 / Tab切换 ---------------------------------------------- */
  useEffect(() => {
    setPage(1)
    setList([])
    setHasMore(true)
    setLoadingMore(false)
    setStatus('loading')
    loadingRef.current = false
    fetchData(1, false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  /* ---- 每日推荐查看计数 ---- */
  useEffect(() => {
    if (activeTab === 'square' || activeTab === 'ai') {
      const d = new Date()
      const key = `daily_recommend_views_${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`
      const current = Number(Taro.getStorageSync(key) || 0)
      if (current >= DAILY_LIMIT) {
        setDailyUsedCount(current)
        return
      }
      const newCount = current + 1
      Taro.setStorageSync(key, newCount)
      setDailyUsedCount(newCount)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  /* ---- 下拉加载更多 ---------------------------------------------------- */
  const handleLoadMore = useCallback(async () => {
    if (loadingRef.current || !hasMore || activeTab === 'ai') return
    loadingRef.current = true
    setLoadingMore(true)

    const nextPage = page + 1
    setPage(nextPage)
    await fetchData(nextPage, true)

    loadingRef.current = false
    setLoadingMore(false)
  }, [page, hasMore, activeTab, fetchData])

  /* ---- 重新加载 -------------------------------------------------------- */
  const handleRefresh = useCallback(() => {
    setPage(1)
    setStatus('loading')
    setErrorMsg('')
    loadingRef.current = false
    fetchData(1, false)
  }, [fetchData])

  /* ---- 跳转详情 -------------------------------------------------------- */
  const goToDetail = useCallback((item: SupplyDemandItem) => {
    Taro.navigateTo({
      url: `/pages/supply-demand/detail/index?id=${item.id}`,
    })
  }, [])

  /* ---- 跳转发布 -------------------------------------------------------- */
  const goToPublish = useCallback(() => {
    Taro.navigateTo({ url: '/pages/post-need/index' })
  }, [])

  /* ---- 联系 / 匹配（详情内也有按钮，这里做快捷操作） --------------------- */
  const handleContact = useCallback((e: any, item: SupplyDemandItem) => {
    e.stopPropagation()
    if (item.contact) {
      Taro.setClipboardData({ data: item.contact })
      Taro.showToast({ title: '联系方式已复制', icon: 'success' })
    } else {
      Taro.showToast({ title: '暂无联系方式', icon: 'none' })
    }
  }, [])

  /* ====================================================================== */
  /*  渲染：各状态                                                           */
  /* ====================================================================== */

  /* --- Loading 骨架屏 --- */
  if (status === 'loading') {
    return (
      <View className='supply-demand'>
        <View className='supply-demand__tabs'>
          {TABS.map((tab) => (
            <View
              key={tab.key}
              className={`supply-demand__tab ${activeTab === tab.key ? 'supply-demand__tab--active' : ''}`}
            >
              {tab.label}
            </View>
          ))}
        </View>
        <View className='supply-demand__skeleton'>
          {[1, 2, 3, 4].map((i) => (
            <View key={i} className='supply-demand__skeleton-item'>
              <View className='supply-demand__skeleton-line supply-demand__skeleton-line--title' />
              <View className='supply-demand__skeleton-line supply-demand__skeleton-line--company' />
              <View className='supply-demand__skeleton-row'>
                <View className='supply-demand__skeleton-line supply-demand__skeleton-line--tag' />
                <View className='supply-demand__skeleton-line supply-demand__skeleton-line--score' />
              </View>
            </View>
          ))}
        </View>
      </View>
    )
  }

  /* --- Error 状态 --- */
  if (status === 'error') {
    return (
      <View className='supply-demand'>
        <View className='supply-demand__tabs'>
          {TABS.map((tab) => (
            <View
              key={tab.key}
              className={`supply-demand__tab ${activeTab === tab.key ? 'supply-demand__tab--active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </View>
          ))}
        </View>
        <View className='supply-demand__error'>
          <Text className='supply-demand__error-icon'>😵</Text>
          <Text className='supply-demand__error-title'>加载失败</Text>
          <Text className='supply-demand__error-msg'>{errorMsg || '请检查网络后重试'}</Text>
          <Button className='supply-demand__error-btn' onClick={handleRefresh}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  /* --- Empty 状态 --- */
  if (status === 'empty') {
    return (
      <View className='supply-demand'>
        <View className='supply-demand__tabs'>
          {TABS.map((tab) => (
            <View
              key={tab.key}
              className={`supply-demand__tab ${activeTab === tab.key ? 'supply-demand__tab--active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </View>
          ))}
        </View>
        <View className='supply-demand__empty'>
          <Text className='supply-demand__empty-icon'>
            {activeTab === 'ai' ? '🤖' : activeTab === 'mine' ? '📋' : '📭'}
          </Text>
          <Text className='supply-demand__empty-title'>
            {activeTab === 'ai'
              ? '暂无AI推荐'
              : activeTab === 'mine'
                ? '您还没有发布供需'
                : '暂无供需信息'}
          </Text>
          <Text className='supply-demand__empty-desc'>
            {activeTab === 'ai'
              ? '请先创建名片，AI将为您智能匹配'
              : '点击下方按钮发布您的供需信息'}
          </Text>
          {activeTab !== 'ai' && (
            <Button className='supply-demand__empty-btn' onClick={goToPublish}>
              发布供需
            </Button>
          )}
          {activeTab === 'square' && (
            <Button className='supply-demand__empty-btn' onClick={handleRefresh}>
              重新加载
            </Button>
          )}
        </View>
      </View>
    )
  }

  /* ====================================================================== */
  /*  渲染：主内容                                                           */
  /* ====================================================================== */

  return (
    <View className='supply-demand'>
      {/* ================ Tab 栏 ================ */}
      <View className='supply-demand__tabs'>
        {TABS.map((tab) => (
          <View
            key={tab.key}
            className={`supply-demand__tab ${activeTab === tab.key ? 'supply-demand__tab--active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            <Text className='supply-demand__tab-label'>{tab.label}</Text>
            {activeTab === tab.key && <View className='supply-demand__tab-indicator' />}
          </View>
        ))}
      </View>

      {/* ================ 每日推荐剩余次数 ================ */}
      {(activeTab === 'ai' || activeTab === 'square') && (
        <View className='supply-demand__daily-remaining'>
          <Text className='supply-demand__daily-remaining-text'>
            今日剩余推荐: {dailyRemaining}/{DAILY_LIMIT}
          </Text>
        </View>
      )}

      {/* ================ AI推荐顶部说明 ================ */}
      {activeTab === 'ai' && list.length > 0 && (
        <View className='supply-demand__ai-header'>
          <Text className='supply-demand__ai-header-icon'>🤖</Text>
          <Text className='supply-demand__ai-header-text'>
            AI基于您的名片信息智能匹配，以下为推荐结果
          </Text>
        </View>
      )}

      {/* ================ 发布按钮（非 AI推荐） ================ */}
      {activeTab !== 'ai' && (
        <View className='supply-demand__publish-bar'>
          <Button className='supply-demand__publish-btn' onClick={goToPublish}>
            ＋ 发布供需
          </Button>
        </View>
      )}

      {/* ================ 列表（含每日遮罩） ================ */}
      <View className='supply-demand__list-wrapper'>
        {limitExceeded && (activeTab === 'ai' || activeTab === 'square') && (
          <View className='supply-demand__limit-overlay'>
            <Text className='supply-demand__limit-overlay-icon'>🔒</Text>
            <Text className='supply-demand__limit-overlay-text'>今日免费次数已用完</Text>
            <Button
              className='supply-demand__limit-overlay-btn'
              onClick={() => Taro.navigateTo({ url: '/pages/membership/index' })}
            >
              升级会员获取无限推荐
            </Button>
          </View>
        )}
      <ScrollView
        className='supply-demand__scroll'
        scrollY
        enhanced
        showScrollbar={false}
        lowerThreshold={80}
        onScrollToLower={handleLoadMore}
      >
        <View className='supply-demand__list'>
          {list.map((item, index) => (
            <View
              key={item.id || index}
              className='supply-demand__card'
              hoverClass='supply-demand__card--active'
              onClick={() => goToDetail(item)}
            >
              {/* 头部：标题 + 匹配度 */}
              <View className='supply-demand__card-header'>
                <Text className='supply-demand__card-title' numberOfLines={1}>
                  {item.title}
                </Text>
                {activeTab === 'ai' && item.match_score > 0 && (
                  <View className='supply-demand__match-badge'>
                    <Text
                      className={`supply-demand__match-value ${
                        item.match_score >= 80
                          ? 'supply-demand__match-value--high'
                          : item.match_score >= 60
                            ? 'supply-demand__match-value--mid'
                            : 'supply-demand__match-value--low'
                      }`}
                    >
                      {item.match_score}%
                    </Text>
                    <Text className='supply-demand__match-label'>匹配</Text>
                  </View>
                )}
                {activeTab !== 'ai' && item.match_score > 0 && (
                  <View className='supply-demand__match-badge supply-demand__match-badge--sm'>
                    <Text className='supply-demand__match-value'>{item.match_score}%</Text>
                  </View>
                )}
              </View>

              {/* 公司 + 行业 */}
              <View className='supply-demand__card-meta'>
                {item.company && (
                  <Text className='supply-demand__card-company' numberOfLines={1}>
                    🏢 {item.company}
                  </Text>
                )}
                {item.industry && (
                  <Text className='supply-demand__card-industry' numberOfLines={1}>
                    📂 {item.industry}
                  </Text>
                )}
              </View>

              {/* 描述（截取） */}
              {item.description && (
                <Text className='supply-demand__card-desc' numberOfLines={2}>
                  {item.description}
                </Text>
              )}

              {/* AI推荐理由 */}
              {item.match_reason && activeTab === 'ai' && (
                <View className='supply-demand__card-reason'>
                  <Text className='supply-demand__card-reason-icon'>💡</Text>
                  <Text className='supply-demand__card-reason-text'>{item.match_reason}</Text>
                </View>
              )}

              {/* 底部：发布时间 + 操作 */}
              <View className='supply-demand__card-footer'>
                <Text className='supply-demand__card-time'>
                  {item.publish_time
                    ? formatTime(item.publish_time)
                    : ''}
                </Text>
                <View className='supply-demand__card-actions'>
                  {activeTab === 'ai' &&
                    (() => {
                      const doneList: string[] = Taro.getStorageSync('feedback_done') || []
                      const isDone = doneList.includes(item.id)
                      return [
                        <Text
                          key='like'
                          className={`supply-demand__card-action supply-demand__feedback-btn ${isDone ? 'supply-demand__feedback-btn--done' : ''}`}
                          onClick={(e) => {
                            e.stopPropagation()
                            if (!isDone) handleFeedback(item.id, 1)
                          }}
                        >
                          👍 有用
                        </Text>,
                        <Text
                          key='dislike'
                          className={`supply-demand__card-action supply-demand__feedback-btn ${isDone ? 'supply-demand__feedback-btn--done' : ''}`}
                          onClick={(e) => {
                            e.stopPropagation()
                            if (!isDone) handleFeedback(item.id, -1)
                          }}
                        >
                          👎 不感兴趣
                        </Text>,
                      ]
                    })()}
                  <Text
                    className='supply-demand__card-action'
                    onClick={(e) => handleContact(e, item)}
                  >
                    联系
                  </Text>
                  <Text className='supply-demand__card-action supply-demand__card-action--primary'>
                    匹配
                  </Text>
                </View>
              </View>
            </View>
          ))}
        </View>

        {/* 加载更多指示器 */}
        {loadingMore && (
          <View className='supply-demand__loading-more'>
            <View className='supply-demand__loading-spinner' />
            <Text className='supply-demand__loading-text'>加载中…</Text>
          </View>
        )}

        {!hasMore && list.length > 0 && (
          <View className='supply-demand__no-more'>
            <Text className='supply-demand__no-more-text'>— 已经到底了 —</Text>
          </View>
        )}

        {/* 底部避让 TabBar */}
        <View className='supply-demand__bottom-spacer' />
      </ScrollView>
      </View>
    </View>
  )
}

export default SupplyDemand

/* ========================================================================== */
/*  工具函数                                                                   */
/* ========================================================================== */

/** 格式化时间为相对时间或日期 */
function formatTime(timeStr: string): string {
  if (!timeStr) return ''
  try {
    const date = new Date(timeStr)
    const now = Date.now()
    const diff = now - date.getTime()

    if (diff < 0) return '刚刚'
    if (diff < 60_000) return '刚刚'
    if (diff < 3600_000) return `${Math.floor(diff / 60_000)}分钟前`
    if (diff < 86_400_000) return `${Math.floor(diff / 3600_000)}小时前`
    if (diff < 604_800_000) return `${Math.floor(diff / 86_400_000)}天前`

    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    return `${y}-${m}-${d}`
  } catch {
    return timeStr
  }
}
