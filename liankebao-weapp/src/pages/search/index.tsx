import { FC, useState, useEffect, useCallback } from 'react'
import { View, Text, Image, Input, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import './index.scss'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

interface SearchResult {
  id: string
  type: 'product' | 'card' | 'supplyDemand'
  title: string
  subtitle?: string
  cover?: string
  tags?: string[]
  description?: string
  status?: string
}

interface HistoryItem {
  keyword: string
  timestamp: number
}

/* ========================================================================== */
/*  常量                                                                       */
/* ========================================================================== */

const HISTORY_KEY = 'search_history'
const MAX_HISTORY = 10

const SEARCH_TABS = [
  { key: 'all', label: '全部' },
  { key: 'product', label: '产品' },
  { key: 'card', label: '名片' },
  { key: 'supplyDemand', label: '供需' },
]

/* ========================================================================== */
/*  Demo 数据                                                                  */
/* ========================================================================== */

const DEMO_RESULTS: SearchResult[] = [
  {
    id: 'r_1',
    type: 'product',
    title: '智能名片 Pro',
    subtitle: '链客科技',
    cover: PLACEHOLDER.cover280x200,
    tags: ['名片', 'AI', '智能'],
    description: 'AI驱动的智能数字名片，支持OCR识别、多模板切换、一键分享。',
  },
  {
    id: 'r_2',
    type: 'product',
    title: 'AI 智能匹配引擎',
    subtitle: '链客科技',
    cover: PLACEHOLDER.cover280x200,
    tags: ['AI', '匹配', '推荐'],
    description: '基于深度学习的商业匹配引擎，精准推荐潜在合作伙伴。',
  },
  {
    id: 'r_3',
    type: 'product',
    title: '营销推广助手',
    subtitle: '链客科技',
    cover: PLACEHOLDER.cover280x200,
    tags: ['营销', '推广', '获客'],
    description: '多渠道营销推广工具，精准触达目标客户群体。',
  },
  {
    id: 'r_4',
    type: 'card',
    title: '张三 · CEO',
    subtitle: '星辰科技有限公司',
    cover: PLACEHOLDER.cover280x200,
    tags: ['科技', 'AI'],
    description: '专注人工智能领域，寻求技术合作与商业落地。',
  },
  {
    id: 'r_5',
    type: 'card',
    title: '李四 · 市场总监',
    subtitle: '云帆传媒集团',
    cover: PLACEHOLDER.cover280x200,
    tags: ['传媒', '营销'],
    description: '十年营销经验，擅长品牌策划与新媒体运营。',
  },
  {
    id: 'r_6',
    type: 'supplyDemand',
    title: '寻找AI技术合作伙伴',
    subtitle: '需求 · 王五',
    tags: ['AI', '技术合作'],
    description: '寻找有NLP或计算机视觉技术团队，共同开发智能客服产品。',
    status: '进行中',
  },
  {
    id: 'r_7',
    type: 'supplyDemand',
    title: '提供企业级CRM系统',
    subtitle: '供给 · 赵六',
    tags: ['CRM', '企业服务'],
    description: '提供定制化CRM系统开发服务，支持私有化部署。',
    status: '进行中',
  },
  {
    id: 'r_8',
    type: 'supplyDemand',
    title: '急需UI设计师合作',
    subtitle: '需求 · 钱七',
    tags: ['UI', '设计'],
    description: '创业团队寻找兼职UI设计师，报酬优厚。',
    status: '进行中',
  },
]

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Search: FC = () => {
  /* ---- 状态 ---- */
  const [keyword, setKeyword] = useState('')
  const [activeTab, setActiveTab] = useState('all')
  const [results, setResults] = useState<SearchResult[]>([])
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [showHistory, setShowHistory] = useState(true)
  const [searched, setSearched] = useState(false)

  /* ---- 加载历史记录 ---- */
  useEffect(() => {
    try {
      const saved = Taro.getStorageSync(HISTORY_KEY)
      if (saved) {
        setHistory(JSON.parse(saved))
      }
    } catch {
      // 静默失败
    }
  }, [])

  /* ---- 保存历史记录 ---- */
  const saveHistory = useCallback(
    (kw: string) => {
      const trimmed = kw.trim()
      if (!trimmed) return

      const updated = [
        { keyword: trimmed, timestamp: Date.now() },
        ...history.filter((h) => h.keyword !== trimmed),
      ].slice(0, MAX_HISTORY)

      setHistory(updated)
      try {
        Taro.setStorageSync(HISTORY_KEY, JSON.stringify(updated))
      } catch {
        // 静默失败
      }
    },
    [history],
  )

  /* ---- 清空历史记录 ---- */
  const clearHistory = useCallback(() => {
    setHistory([])
    try {
      Taro.removeStorageSync(HISTORY_KEY)
    } catch {
      // 静默失败
    }
  }, [])

  /* ---- 删除单条历史 ---- */
  const removeHistoryItem = useCallback(
    (kw: string) => {
      const updated = history.filter((h) => h.keyword !== kw)
      setHistory(updated)
      try {
        Taro.setStorageSync(HISTORY_KEY, JSON.stringify(updated))
      } catch {
        // 静默失败
      }
    },
    [history],
  )

  /* ---- 执行搜索 ---- */
  const doSearch = useCallback(
    (kw: string) => {
      const trimmed = kw.trim()
      if (!trimmed) return

      saveHistory(trimmed)
      setKeyword(trimmed)
      setShowHistory(false)
      setSearched(true)

      // 内置搜索 (demo data)
      const lower = trimmed.toLowerCase()
      let filtered = DEMO_RESULTS.filter(
        (item) =>
          item.title.toLowerCase().includes(lower) ||
          (item.subtitle && item.subtitle.toLowerCase().includes(lower)) ||
          (item.description && item.description.toLowerCase().includes(lower)) ||
          (item.tags && item.tags.some((t) => t.toLowerCase().includes(lower))),
      )

      // 标签筛选
      if (activeTab !== 'all') {
        filtered = filtered.filter((item) => item.type === activeTab)
      }

      setResults(filtered)
    },
    [saveHistory, activeTab],
  )

  /* ---- 搜索输入 ---- */
  const onSearchInput = useCallback((e: any) => {
    const val = e.detail.value
    setKeyword(val)
    if (!val.trim()) {
      setShowHistory(true)
      setSearched(false)
      setResults([])
    }
  }, [])

  /* ---- 确认搜索 ---- */
  const onSearchConfirm = useCallback(() => {
    doSearch(keyword)
  }, [doSearch, keyword])

  /* ---- 点击历史记录 ---- */
  const onHistoryClick = useCallback(
    (kw: string) => {
      setKeyword(kw)
      doSearch(kw)
    },
    [doSearch],
  )

  /* ---- 切换标签 ---- */
  const switchTab = useCallback(
    (key: string) => {
      setActiveTab(key)
      if (searched) {
        // 重新筛选当前结果
        const lower = keyword.trim().toLowerCase()
        let filtered = DEMO_RESULTS.filter(
          (item) =>
            item.title.toLowerCase().includes(lower) ||
            (item.subtitle && item.subtitle.toLowerCase().includes(lower)) ||
            (item.description && item.description.toLowerCase().includes(lower)) ||
            (item.tags && item.tags.some((t) => t.toLowerCase().includes(lower))),
        )
        if (key !== 'all') {
          filtered = filtered.filter((item) => item.type === key)
        }
        setResults(filtered)
      }
    },
    [keyword, searched],
  )

  /* ---- 清除搜索 ---- */
  const clearSearch = useCallback(() => {
    setKeyword('')
    setShowHistory(true)
    setSearched(false)
    setResults([])
  }, [])

  /* ---- 点击结果详情 ---- */
  const goToDetail = useCallback((item: SearchResult) => {
    switch (item.type) {
      case 'product':
        Taro.navigateTo({ url: `/pages/product/detail/index?id=${item.id}` })
        break
      case 'card':
        Taro.navigateTo({ url: `/pages/card-detail/index?id=${item.id}` })
        break
      case 'supplyDemand':
        Taro.navigateTo({ url: `/pages/supply-demand/detail/index?id=${item.id}` })
        break
      default:
        Taro.showToast({ title: item.title, icon: 'none' })
    }
  }, [])

  /* ---- 获取类型标签样式 ---- */
  const getTypeTag = (type: string) => {
    switch (type) {
      case 'product':
        return { label: '产品', className: 'search__type-tag--product' }
      case 'card':
        return { label: '名片', className: 'search__type-tag--card' }
      case 'supplyDemand':
        return { label: '供需', className: 'search__type-tag--supply' }
      default:
        return { label: type, className: '' }
    }
  }

  /* ================================================================ */
  /*  渲染                                                                  */
  /* ================================================================ */

  return (
    <View className='search'>
      {/* ================ 搜索栏 ================ */}
      <View className='search__bar'>
        <View className='search__input-wrap'>
          <Text className='search__input-icon'>🔍</Text>
          <Input
            className='search__input'
            type='text'
            placeholder='搜索产品、名片、供需...'
            value={keyword}
            onInput={onSearchInput}
            onConfirm={onSearchConfirm}
            confirmType='search'
          />
          {keyword && (
            <Text className='search__input-clear' onClick={clearSearch}>
              ✕
            </Text>
          )}
        </View>
        <Button className='search__bar-btn' onClick={onSearchConfirm}>
          搜索
        </Button>
      </View>

      {/* ================ 历史搜索 ================ */}
      {showHistory && (
        <ScrollView
          className='search__body'
          scrollY
          enhanced
          showScrollbar={false}
        >
          {history.length > 0 && (
            <View className='search__history'>
              <View className='search__history-header'>
                <Text className='search__history-title'>历史搜索</Text>
                <Text className='search__history-clear' onClick={clearHistory}>
                  清空
                </Text>
              </View>
              <View className='search__history-list'>
                {history.map((item) => (
                  <View
                    key={`${item.keyword}_${item.timestamp}`}
                    className='search__history-item'
                    onClick={() => onHistoryClick(item.keyword)}
                  >
                    <Text className='search__history-item-icon'>🕐</Text>
                    <Text className='search__history-item-text'>
                      {item.keyword}
                    </Text>
                    <Text
                      className='search__history-item-del'
                      onClick={(e) => {
                        e.stopPropagation()
                        removeHistoryItem(item.keyword)
                      }}
                    >
                      ✕
                    </Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* 热门推荐 */}
          <View className='search__hot'>
            <Text className='search__hot-title'>热门搜索</Text>
            <View className='search__hot-list'>
              {['智能名片', 'AI匹配', '营销推广', 'CRM', 'UI设计', '技术合作'].map(
                (tag) => (
                  <View
                    key={tag}
                    className='search__hot-tag'
                    onClick={() => onHistoryClick(tag)}
                  >
                    <Text>{tag}</Text>
                  </View>
                ),
              )}
            </View>
          </View>

          {/* 底部提示 */}
          <View className='search__body-spacer' />
        </ScrollView>
      )}

      {/* ================ 搜索结果 ================ */}
      {!showHistory && (
        <View className='search__results'>
          {/* 标签切换 */}
          <View className='search__tabs'>
            {SEARCH_TABS.map((tab) => (
              <View
                key={tab.key}
                className={`search__tab ${activeTab === tab.key ? 'search__tab--active' : ''}`}
                onClick={() => switchTab(tab.key)}
              >
                <Text className='search__tab-label'>{tab.label}</Text>
              </View>
            ))}
          </View>

          <ScrollView
            className='search__results-scroll'
            scrollY
            enhanced
            showScrollbar={false}
            lowerThreshold={50}
          >
            {results.length > 0 ? (
              <View className='search__results-list'>
                {results.map((item) => {
                  const tag = getTypeTag(item.type)
                  return (
                    <View
                      key={item.id}
                      className='search__result-card'
                      onClick={() => goToDetail(item)}
                    >
                      {/* 封面图 */}
                      {item.cover && (
                        <Image
                          className='search__result-cover'
                          src={item.cover}
                          mode='aspectFill'
                        />
                      )}
                      {/* 信息区 */}
                      <View className='search__result-info'>
                        <View className='search__result-top'>
                          <Text className='search__result-title'>
                            {item.title}
                          </Text>
                          <Text className={`search__type-tag ${tag.className}`}>
                            {tag.label}
                          </Text>
                        </View>
                        {item.subtitle && (
                          <Text className='search__result-subtitle'>
                            {item.subtitle}
                          </Text>
                        )}
                        {item.description && (
                          <Text
                            className='search__result-desc'
                            numberOfLines={2}
                          >
                            {item.description}
                          </Text>
                        )}
                        {/* 标签 */}
                        {item.tags && item.tags.length > 0 && (
                          <View className='search__result-tags'>
                            {item.tags.slice(0, 3).map((tag) => (
                              <Text key={tag} className='search__result-tag'>
                                {tag}
                              </Text>
                            ))}
                          </View>
                        )}
                      </View>
                    </View>
                  )
                })}
              </View>
            ) : (
              <View className='search__empty'>
                <Text className='search__empty-icon'>🔍</Text>
                <Text className='search__empty-title'>未找到相关结果</Text>
                <Text className='search__empty-desc'>
                  换个关键词试试
                </Text>
              </View>
            )}

            {/* 搜索统计 */}
            {results.length > 0 && (
              <View className='search__stats'>
                <Text className='search__stats-text'>
                  共找到 {results.length} 条结果
                </Text>
              </View>
            )}

            <View className='search__bottom-spacer' />
          </ScrollView>
        </View>
      )}
    </View>
  )
}

export default Search
