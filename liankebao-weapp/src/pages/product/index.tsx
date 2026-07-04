import { FC, useState, useEffect, useCallback } from 'react'
import { View, Text, Image, Input, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { appStoreApi } from '../../api/digitalBrochure'
import './index.scss'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

/** 产品/插件数据 */
interface ProductItem {
  id: string
  /** 封面图 */
  cover?: string
  /** 产品名称 */
  name: string
  /** 价格描述 */
  price?: string
  /** 供应商/开发者 */
  supplier?: string
  /** 分类 */
  category?: string
  /** 标签 */
  tags?: string[]
  /** 产品描述 */
  description?: string
  /** 产品参数 */
  params?: Record<string, string>
  /** 联系方式 */
  contact?: string
  /** 评分 */
  rating?: number
  [key: string]: any
}

type PageStatus = 'loading' | 'ready' | 'error'

/* ========================================================================== */
/*  常量 — 分类筛选                                                           */
/* ========================================================================== */

const CATEGORIES = [
  { key: 'all', label: '全部' },
  { key: 'digital_card', label: '数字名片' },
  { key: 'ai_tools', label: 'AI 工具' },
  { key: 'marketing', label: '营销推广' },
  { key: 'crm', label: '客户管理' },
  { key: 'analytics', label: '数据分析' },
]

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Product: FC = () => {
  /* ---- 状态 ---- */
  const [status, setStatus] = useState<PageStatus>('loading')
  const [products, setProducts] = useState<ProductItem[]>([])
  const [filteredProducts, setFilteredProducts] = useState<ProductItem[]>([])
  const [activeCategory, setActiveCategory] = useState('all')
  const [searchKeyword, setSearchKeyword] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  /* ---- 加载产品列表 ---- */
  const loadProducts = useCallback(async () => {
    try {
      const res = await appStoreApi.getPlugins()
      if (res.code === 200 || res.code === 0) {
        const list = (res.data as any)?.list ?? (res.data as any) ?? []
        setProducts(list)
        setFilteredProducts(list)
      } else {
        // fallback demo data
        setProducts(DEMO_PRODUCTS)
        setFilteredProducts(DEMO_PRODUCTS)
      }
    } catch {
      // fallback demo data
      setProducts(DEMO_PRODUCTS)
      setFilteredProducts(DEMO_PRODUCTS)
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
      await loadProducts()
      setStatus('ready')
    } catch (e: any) {
      setErrorMsg(e.message || '加载产品失败')
      setStatus('error')
    }
  }

  /* ---- 分类筛选 + 搜索 ---- */
  useEffect(() => {
    let result = products

    // 分类筛选
    if (activeCategory !== 'all') {
      result = result.filter(
        (p) => p.category === activeCategory || (p.tags && p.tags.includes(activeCategory)),
      )
    }

    // 关键字搜索
    if (searchKeyword.trim()) {
      const kw = searchKeyword.trim().toLowerCase()
      result = result.filter(
        (p) =>
          p.name.toLowerCase().includes(kw) ||
          (p.supplier && p.supplier.toLowerCase().includes(kw)) ||
          (p.description && p.description.toLowerCase().includes(kw)),
      )
    }

    setFilteredProducts(result)
  }, [activeCategory, searchKeyword, products])

  /* ---- 切换分类 ---- */
  const switchCategory = useCallback((key: string) => {
    setActiveCategory(key)
  }, [])

  /* ---- 搜索输入 ---- */
  const onSearchInput = useCallback((e: any) => {
    setSearchKeyword(e.detail.value)
  }, [])

  /* ---- 点击产品详情 ---- */
  const goToDetail = useCallback((product: ProductItem) => {
    Taro.navigateTo({
      url: `/pages/product/detail/index?id=${product.id}`,
    })
  }, [])

  /* ---- 发布产品 ---- */
  const publishProduct = useCallback(() => {
    Taro.navigateTo({ url: '/pages/product/publish/index' })
  }, [])

  /* ---- 联系供应商 ---- */
  const contactSupplier = useCallback((supplier?: string) => {
    if (supplier) {
      Taro.showToast({ title: `联系: ${supplier}`, icon: 'none' })
    }
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
      <View className='product'>
        <View className='product__skeleton'>
          <View className='product__skeleton-search' />
          <View className='product__skeleton-categories'>
            {[1, 2, 3, 4].map((i) => (
              <View key={i} className='product__skeleton-cat' />
            ))}
          </View>
          <View className='product__skeleton-list'>
            {[1, 2, 3, 4].map((i) => (
              <View key={i} className='product__skeleton-item' />
            ))}
          </View>
        </View>
      </View>
    )
  }

  if (status === 'error') {
    return (
      <View className='product'>
        <View className='product__error'>
          <Text className='product__error-icon'>😵</Text>
          <Text className='product__error-title'>加载失败</Text>
          <Text className='product__error-message'>{errorMsg || '请检查网络后重试'}</Text>
          <Button className='product__error-btn' onClick={onRefresh}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  return (
    <View className='product'>
      {/* ================ 搜索栏 ================ */}
      <View className='product__search-bar'>
        <View className='product__search-input-wrap'>
          <Text className='product__search-icon'>🔍</Text>
          <Input
            className='product__search-input'
            type='text'
            placeholder='搜索产品、供应商...'
            value={searchKeyword}
            onInput={onSearchInput}
            confirmType='search'
          />
          {searchKeyword && (
            <Text className='product__search-clear' onClick={() => setSearchKeyword('')}>
              ✕
            </Text>
          )}
        </View>
      </View>

      <ScrollView
        className='product__scroll'
        scrollY
        enhanced
        showScrollbar={false}
        lowerThreshold={50}
        onScrollToLower={() => {}}
      >
        {/* ================ 分类筛选 ================ */}
        <View className='product__categories'>
          <ScrollView className='product__categories-scroll' scrollX enhanced showScrollbar={false}>
            {CATEGORIES.map((cat) => (
              <View
                key={cat.key}
                className={`product__category-tab ${activeCategory === cat.key ? 'product__category-tab--active' : ''}`}
                onClick={() => switchCategory(cat.key)}
              >
                <Text className='product__category-label'>{cat.label}</Text>
              </View>
            ))}
          </ScrollView>
        </View>

        {/* ================ 产品列表 ================ */}
        {filteredProducts.length > 0 ? (
          <View className='product__list'>
            {filteredProducts.map((product) => (
              <View
                key={product.id}
                className='product__card'
                onClick={() => goToDetail(product)}
              >
                {/* 封面图 */}
                <Image
                  className='product__card-cover'
                  src={product.cover || PLACEHOLDER.cover280x200}
                  mode='aspectFill'
                />
                {/* 信息区 */}
                <View className='product__card-info'>
                  <Text className='product__card-name'>{product.name}</Text>
                  {product.price && (
                    <Text className='product__card-price'>{product.price}</Text>
                  )}
                  {product.supplier && (
                    <Text className='product__card-supplier'>
                      供应商: {product.supplier}
                    </Text>
                  )}
                  {product.description && (
                    <Text className='product__card-desc' numberOfLines={2}>
                      {product.description}
                    </Text>
                  )}
                  {/* 标签 */}
                  {product.tags && product.tags.length > 0 && (
                    <View className='product__card-tags'>
                      {product.tags.slice(0, 3).map((tag) => (
                        <Text key={tag} className='product__card-tag'>
                          {tag}
                        </Text>
                      ))}
                    </View>
                  )}
                  {/* 联系供应商按钮 */}
                  <Button
                    className='product__card-contact-btn'
                    onClick={(e) => {
                      e.stopPropagation()
                      contactSupplier(product.supplier || product.contact)
                    }}
                  >
                    联系供应商
                  </Button>
                </View>
              </View>
            ))}
          </View>
        ) : (
          <View className='product__empty'>
            <Text className='product__empty-icon'>📦</Text>
            <Text className='product__empty-title'>暂无产品</Text>
            <Text className='product__empty-desc'>换个分类或关键词试试</Text>
          </View>
        )}

        {/* 底部间距 */}
        <View className='product__bottom-spacer' />
      </ScrollView>

      {/* ================ 发布产品 FAB ================ */}
      <View className='product__fab' onClick={publishProduct}>
        <Text className='product__fab-icon'>＋</Text>
        <Text className='product__fab-label'>发布产品</Text>
      </View>
    </View>
  )
}

/* ========================================================================== */
/*  Demo 数据 (API 不可用时的降级展示)                                         */
/* ========================================================================== */

const DEMO_PRODUCTS: ProductItem[] = [
  {
    id: 'demo_1',
    name: '智能名片 Pro',
    cover: PLACEHOLDER.cover280x200,
    price: '¥99/年',
    supplier: '链客科技',
    category: 'digital_card',
    tags: ['名片', 'AI', '智能'],
    description: 'AI驱动的智能数字名片，支持OCR识别、多模板切换、一键分享。',
    rating: 4.8,
  },
  {
    id: 'demo_2',
    name: 'AI 智能匹配引擎',
    cover: PLACEHOLDER.cover280x200,
    price: '¥299/年',
    supplier: '链客科技',
    category: 'ai_tools',
    tags: ['AI', '匹配', '推荐'],
    description: '基于深度学习的商业匹配引擎，精准推荐潜在合作伙伴。',
    rating: 4.6,
  },
  {
    id: 'demo_3',
    name: '营销推广助手',
    cover: PLACEHOLDER.cover280x200,
    price: '¥199/年',
    supplier: '链客科技',
    category: 'marketing',
    tags: ['营销', '推广', '获客'],
    description: '多渠道营销推广工具，精准触达目标客户群体。',
    rating: 4.5,
  },
  {
    id: 'demo_4',
    name: '客户管理 CRM',
    cover: PLACEHOLDER.cover280x200,
    price: '¥399/年',
    supplier: '链客科技',
    category: 'crm',
    tags: ['CRM', '客户', '管理'],
    description: '轻量级CRM系统，管理客户关系与商机跟进。',
    rating: 4.7,
  },
]

export default Product
