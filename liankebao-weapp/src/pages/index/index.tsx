import { FC, useState, useEffect, useCallback } from 'react'
import { View, Text, Image, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import FlipBook from '../../components/FlipBook'
import cardApi, { CardData } from '../../api/card'
import matchApi, { RecommendItem } from '../../api/match'
import userApi, { UserInfo } from '../../api/user'
import './index.scss'
import AiRecommend from '../../components/AiRecommend'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

type PageStatus = 'loading' | 'ready' | 'error' | 'noLogin'

/* ========================================================================== */
/*  常量                                                                       */
/* ========================================================================== */

const QUICK_ENTRIES = [
  {
    key: 'market',
    title: '供需大厅',
    subtitle: '找资源 · 找合作',
    icon: '🏪',
    gradient: 'linear-gradient(135deg, #1677ff 0%, #0958d9 100%)',
    url: '/pages/market/index',
  },
  {
    key: 'products',
    title: '产品池',
    subtitle: '展示优质产品',
    icon: '📦',
    gradient: 'linear-gradient(135deg, #fa8c16 0%, #d46b08 100%)',
    url: '/pages/products/index',
  },
  {
    key: 'promotion',
    title: '推广中心',
    subtitle: '精准推广获客',
    icon: '📢',
    gradient: 'linear-gradient(135deg, #52c41a 0%, #389e0d 100%)',
    url: '/pages/promotion/index',
  },
]

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Index: FC = () => {
  /* ---- 状态 ---- */
  const [status, setStatus] = useState<PageStatus>('loading')
  const [user, setUser] = useState<UserInfo | null>(null)
  const [cardList, setCardList] = useState<CardData[]>([])
  const [currentCard, setCurrentCard] = useState<CardData | null>(null)
  const [recommendList, setRecommendList] = useState<RecommendItem[]>([])
  const [errorMsg, setErrorMsg] = useState('')

  /* ---- 加载用户信息 ---- */
  const loadUser = useCallback(async () => {
    try {
      const token = Taro.getStorageSync('token')
      if (!token) {
        setStatus('noLogin')
        return
      }
      const res = await userApi.getMe()
      if (res.code === 200 || res.code === 0) {
        setUser(res.data as unknown as UserInfo)
      } else {
        // token 无效
        Taro.removeStorageSync('token')
        Taro.removeStorageSync('user')
        setStatus('noLogin')
      }
    } catch {
      // 静默失败 — 后续加载卡片时会触发完整状态
    }
  }, [])

  /* ---- 加载名片列表 ---- */
  const loadCards = useCallback(async () => {
    try {
      const res = await cardApi.getList({ page: 1, page_size: 10 })
      const list = (res.data as any)?.list ?? []
      setCardList(list)
      setCurrentCard(list[0] ?? null)
      return list
    } catch (e: any) {
      setErrorMsg(e.message || '加载名片失败')
      setStatus('error')
      return []
    }
  }, [])

  /* ---- 加载AI推荐 ---- */
  const loadRecommend = useCallback(async (cardId: string) => {
    try {
      const res = await matchApi.getHybridRecommend(cardId)
      const items = (res.data as any) ?? []
      setRecommendList(items)
    } catch {
      // 推荐加载失败不阻塞页面
      setRecommendList([])
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

    await loadUser()

    const list = await loadCards()
    if (list.length > 0) {
      setStatus('ready')
      // 加载 AI 推荐
      const token = Taro.getStorageSync('token')
      if (token && list[0]?.id) {
        loadRecommend(list[0].id)
      }
    } else {
      // 没有名片 — 也算 ready 状态，展示创建引导
      setStatus('ready')
    }
  }

  /* ---- 下拉刷新 ---- */
  const onRefresh = useCallback(() => {
    initPage()
  }, [])

  /* ---- 切换名片 ---- */
  const switchCard = useCallback(
    (card: CardData) => {
      setCurrentCard(card)
      if (card?.id) {
        loadRecommend(card.id)
      }
    },
    [loadRecommend],
  )

  /* ---- 跳转名片编辑 ---- */
  const goToCardEditor = useCallback(() => {
    Taro.navigateTo({ url: '/pages/card-editor/index' })
  }, [])

  /* ---- 跳转快速入口 ---- */
  const goToEntry = useCallback((url: string) => {
    Taro.navigateTo({ url })
  }, [])

  /* ---- 跳转登录 ---- */
  const goToLogin = useCallback(() => {
    Taro.navigateTo({ url: '/pages/login/index' })
  }, [])

  /* ---- 跳转推荐详情 ---- */
  const goToRecommendDetail = useCallback((cardId: string) => {
    Taro.navigateTo({ url: `/pages/card-detail/index?id=${cardId}` })
  }, [])

  /* ================================================================ */
  /*  渲染：各状态                                                      */
  /* ================================================================ */

  /* --- Loading 骨架屏 --- */
  if (status === 'loading') {
    return (
      <View className='index'>
        <View className='index__skeleton'>
          <View className='index__skeleton-header'>
            <View className='index__skeleton-avatar' />
            <View className='index__skeleton-info'>
              <View className='index__skeleton-line index__skeleton-line--name' />
              <View className='index__skeleton-line index__skeleton-line--company' />
            </View>
          </View>
          <View className='index__skeleton-card'>
            <View className='index__skeleton-card-placeholder' />
          </View>
          <View className='index__skeleton-entries'>
            {[1, 2, 3].map((i) => (
              <View key={i} className='index__skeleton-entry' />
            ))}
          </View>
        </View>
      </View>
    )
  }

  /* --- 未登录 --- */
  if (status === 'noLogin') {
    return (
      <View className='index'>
        <View className='index__no-login'>
          <View className='index__no-login-icon'>👤</View>
          <Text className='index__no-login-title'>欢迎来到链客宝</Text>
          <Text className='index__no-login-desc'>登录后即可创建您的数字名片</Text>
          <Button className='index__no-login-btn' onClick={goToLogin}>
            立即登录
          </Button>
          <View className='index__no-login-preview'>
            <Text className='index__no-login-preview-title'>预览模式</Text>
            <AiRecommend />
            <FlipBook
              cardData={{
                name: '您的姓名',
                company: '您的公司',
                title: '职位',
                avatar: '',
              }}
              flippable={false}
            />
          </View>
        </View>
      </View>
    )
  }

  /* --- 错误状态 --- */
  if (status === 'error') {
    return (
      <View className='index'>
        <View className='index__error'>
          <Text className='index__error-icon'>😵</Text>
          <Text className='index__error-title'>加载失败</Text>
          <Text className='index__error-message'>{errorMsg || '请检查网络后重试'}</Text>
          <Button className='index__error-btn' onClick={onRefresh}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  /* ================================================================ */
  /*  渲染：主页面                                                      */
  /* ================================================================ */

  return (
    <View className='index'>
      <ScrollView
        className='index__scroll'
        scrollY
        enhanced
        showScrollbar={false}
        lowerThreshold={50}
        onScrollToLower={() => {}}
      >
        {/* ================ 顶部用户信息栏 ================ */}
        <View className='index__header'>
          <View className='index__header-left'>
            <Image
              className='index__avatar'
              src={
                user?.avatar ||
                PLACEHOLDER.avatar80
              }
              mode='aspectFill'
              onClick={() => Taro.navigateTo({ url: '/pages/user/profile/index' })}
            />
            <View className='index__header-info'>
              <Text className='index__user-name'>{user?.nickname || '用户'}</Text>
              <Text className='index__user-company'>
                {[user?.company, user?.title].filter(Boolean).join(' · ') || '点击设置个人信息'}
              </Text>
            </View>
          </View>
          <View
            className='index__header-right'
            onClick={() => Taro.navigateTo({ url: '/pages/user/profile/index' })}
          >
            <Text className='index__settings-icon'>⚙️</Text>
          </View>
        </View>

        {/* ================ 数字名片展示 ================ */}
        <View className='index__card-section'>
          {currentCard ? (
            <>
              <FlipBook cardData={currentCard} flippable />
              {/* 多名片切换指示 */}
              {cardList.length > 1 && (
                <View className='index__card-switch'>
                  {cardList.map((card) => (
                    <View
                      key={card.id}
                      className={`index__card-dot ${card.id === currentCard.id ? 'index__card-dot--active' : ''}`}
                      onClick={() => switchCard(card)}
                    />
                  ))}
                </View>
              )}
            </>
          ) : (
            <FlipBook />
          )}
        </View>

        {/* ================ AI智能创建入口 ================ */}
        <View className='index__ai-section' onClick={goToCardEditor}>
          <View className='index__ai-btn'>
            <View className='index__ai-btn-bg' />
            <View className='index__ai-btn-content'>
              <Text className='index__ai-btn-icon'>✨</Text>
              <View className='index__ai-btn-text'>
                <Text className='index__ai-btn-title'>AI 帮我创建名片</Text>
                <Text className='index__ai-btn-desc'>智能生成 · 一键发布</Text>
              </View>
              <Text className='index__ai-btn-arrow'>›</Text>
            </View>
          </View>
        </View>

        {/* ================ 快速入口 ================ */}
        <View className='index__entries'>
          {QUICK_ENTRIES.map((entry) => (
            <View
              key={entry.key}
              className='index__entry-card'
              onClick={() => goToEntry(entry.url)}
            >
              <View
                className='index__entry-card-bg'
                style={{ background: entry.gradient }}
              />
              <View className='index__entry-card-content'>
                <Text className='index__entry-icon'>{entry.icon}</Text>
                <Text className='index__entry-title'>{entry.title}</Text>
                <Text className='index__entry-subtitle'>{entry.subtitle}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* ================ AI智能推荐 ================ */}
        {recommendList.length > 0 && (
          <View className='index__recommend'>
            <View className='index__recommend-header'>
              <Text className='index__recommend-title'>🤖 智能推荐</Text>
              <Text
                className='index__recommend-more'
                onClick={() => Taro.navigateTo({ url: '/pages/recommend/index' })}
              >
                查看更多 ›
              </Text>
            </View>

            <ScrollView
              className='index__recommend-scroll'
              scrollX
              enhanced
              showScrollbar={false}
            >
              {recommendList.map((item) => (
                <View
                  key={item.id}
                  className='index__recommend-card'
                  onClick={() => goToRecommendDetail(item.card_id)}
                >
                  <View className='index__recommend-card-top'>
                    <Image
                      className='index__recommend-avatar'
                      src={item.avatar || 'https://via.placeholder.com/64'}
                      mode='aspectFill'
                    />
                    <View className='index__recommend-match'>
                      <Text className='index__recommend-match-label'>匹配度</Text>
                      <Text className='index__recommend-match-value'>
                        {Math.round((item.match_score || 0) * 100)}%
                      </Text>
                    </View>
                  </View>
                  <Text className='index__recommend-name'>{item.name}</Text>
                  <Text className='index__recommend-company'>
                    {[item.company, item.title].filter(Boolean).join(' · ')}
                  </Text>
                  {item.match_reason && (
                    <Text className='index__recommend-reason'>{item.match_reason}</Text>
                  )}
                  {item.tags && item.tags.length > 0 && (
                    <View className='index__recommend-tags'>
                      {item.tags.slice(0, 3).map((tag) => (
                        <Text key={tag} className='index__recommend-tag'>
                          {tag}
                        </Text>
                      ))}
                    </View>
                  )}
                </View>
              ))}
            </ScrollView>
          </View>
        )}

        {/* 底部间距（避让TabBar） */}
        <View className='index__bottom-spacer' />
      </ScrollView>
    </View>
  )
}

export default Index
