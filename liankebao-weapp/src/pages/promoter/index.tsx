import {
  FC,
  useState,
  useEffect,
  useCallback,
  useRef,
  useMemo,
} from 'react'
import {
  View,
  Text,
  Image,
  ScrollView,
  Button,
  Canvas,
} from '@tarojs/components'
import Taro from '@tarojs/taro'
import growthApi, {
  MetricsData,
  TrendItem,
  ProductItem,
  SubPromoter,
  EarningsDetail,
} from '../../api/growth'
import './index.scss'

/* ========================================================================== */
/*  类型 & 常量                                                                */
/* ========================================================================== */

type TabKey = 'products' | 'promoters' | 'details'

const TAB_ITEMS: { key: TabKey; label: string }[] = [
  { key: 'products', label: '推广商品' },
  { key: 'promoters', label: '推广员' },
  { key: 'details', label: '收益明细' },
]

/** 分 → 元 */
const toYuan = (fen: number) => (fen / 100).toFixed(2)

/* ========================================================================== */
/*  子组件：柱状图（纯 CSS）                                                    */
/* ========================================================================== */

const BarChart: FC<{ data: TrendItem[] }> = ({ data }) => {
  if (!data || data.length === 0) return null

  const maxVal = Math.max(...data.map((d) => d.earnings), 1)

  return (
    <View className='promoter__chart'>
      <Text className='promoter__chart-title'>近 7 日收益趋势</Text>
      <View className='promoter__chart-bars'>
        {data.map((item) => {
          const pct = (item.earnings / maxVal) * 100
          return (
            <View key={item.date} className='promoter__chart-col'>
              <View className='promoter__chart-bar-wrap'>
                <View
                  className='promoter__chart-bar'
                  style={{ height: `${Math.max(pct, 2)}%` }}
                />
              </View>
              <Text className='promoter__chart-label'>{item.date}</Text>
              <Text className='promoter__chart-value'>¥{toYuan(item.earnings)}</Text>
            </View>
          )
        })}
      </View>
    </View>
  )
}

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Promoter: FC = () => {
  /* ---- 状态 ---- */
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [trends, setTrends] = useState<TrendItem[]>([])
  const [products, setProducts] = useState<ProductItem[]>([])
  const [promoters, setPromoters] = useState<SubPromoter[]>([])
  const [details, setDetails] = useState<EarningsDetail[]>([])
  const [activeTab, setActiveTab] = useState<TabKey>('products')

  /* Canvas 引用（推广海报） */
  const canvasRef = useRef<any>(null)

  /* ---- 数据加载 ---- */
  const loadAll = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [metricsRes, trendsRes] = await Promise.all([
        growthApi.getMetrics(),
        growthApi.getTrends({ days: 7 }),
      ])
      if (metricsRes.code === 200 || metricsRes.code === 0) {
        setMetrics(metricsRes.data as MetricsData)
      }
      if (trendsRes.code === 200 || trendsRes.code === 0) {
        setTrends((trendsRes.data as TrendItem[]) || [])
      }
    } catch (e: any) {
      setError(e.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  const loadProducts = useCallback(async () => {
    try {
      const res = await growthApi.getProducts()
      if (res.code === 200 || res.code === 0) {
        setProducts((res.data as ProductItem[]) || [])
      }
    } catch {
      // 静默
    }
  }, [])

  const loadPromoters = useCallback(async () => {
    try {
      const res = await growthApi.getSubPromoters()
      if (res.code === 200 || res.code === 0) {
        setPromoters((res.data as SubPromoter[]) || [])
      }
    } catch {
      // 静默
    }
  }, [])

  const loadDetails = useCallback(async () => {
    try {
      const res = await growthApi.getEarningsDetails()
      if (res.code === 200 || res.code === 0) {
        setDetails((res.data as EarningsDetail[]) || [])
      }
    } catch {
      // 静默
    }
  }, [])

  useEffect(() => {
    loadAll()
    loadProducts()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (activeTab === 'promoters') loadPromoters()
    if (activeTab === 'details') loadDetails()
  }, [activeTab, loadPromoters, loadDetails])

  /* ---- 复制推广链接 ---- */
  const copyLink = useCallback(
    (product: ProductItem) => {
      Taro.setClipboardData({
        data: product.promo_link,
        success: () => {
          Taro.showToast({ title: '推广链接已复制', icon: 'success' })
        },
      })
    },
    [],
  )

  /* ---- 分享 ---- */
  const shareProduct = useCallback((product: ProductItem) => {
    Taro.shareAppMessage({
      title: `推荐：${product.name}`,
      path: `/pages/product-detail/index?id=${product.id}`,
    })
  }, [])

  /* ---- 绘制推广海报 ---- */
  const drawPoster = useCallback(async () => {
    if (!metrics?.promo_code) return

    try {
      const canvas = canvasRef.current
      if (!canvas) {
        Taro.showToast({ title: 'Canvas 未就绪', icon: 'none' })
        return
      }

      const ctx = canvas.getContext('2d')
      const dpr = Taro.getSystemInfoSync().pixelRatio || 2
      const width = 300 * dpr
      const height = 480 * dpr

      canvas.width = width
      canvas.height = height

      // 背景
      ctx.scale(dpr, dpr)
      const gradient = ctx.createLinearGradient(0, 0, 300, 480)
      gradient.addColorStop(0, '#1677ff')
      gradient.addColorStop(1, '#0958d9')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, 300, 480)

      // 标题
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 22px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText('链客宝 · 推广海报', 150, 60)

      // 推广码
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 32px sans-serif'
      ctx.fillText(metrics.promo_code, 150, 180)

      // 提示
      ctx.fillStyle = 'rgba(255,255,255,0.8)'
      ctx.font = '14px sans-serif'
      ctx.fillText('长按扫码，注册即享专属权益', 150, 230)

      // 装饰线
      ctx.strokeStyle = 'rgba(255,255,255,0.3)'
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(40, 260)
      ctx.lineTo(260, 260)
      ctx.stroke()

      // 收益摘要
      ctx.fillStyle = '#ffffff'
      ctx.font = '16px sans-serif'
      ctx.fillText(`今日收益: ¥${toYuan(metrics.today_earnings)}`, 150, 300)
      ctx.fillText(`本月收益: ¥${toYuan(metrics.month_earnings)}`, 150, 330)
      ctx.fillText(`团队人数: ${metrics.team_size} 人`, 150, 360)

      // 底部水印
      ctx.fillStyle = 'rgba(255,255,255,0.4)'
      ctx.font = '12px sans-serif'
      ctx.fillText('链客宝 · 让推广更简单', 150, 440)

      // 导出为图片
      Taro.canvasToTempFilePath({
        canvas,
        success: (res) => {
          Taro.saveImageToPhotosAlbum({
            filePath: res.tempFilePath,
            success: () => {
              Taro.showToast({ title: '海报已保存', icon: 'success' })
            },
            fail: () => {
              Taro.showToast({ title: '保存失败，请开启相册权限', icon: 'none' })
            },
          })
        },
        fail: () => {
          Taro.showToast({ title: '海报生成失败', icon: 'none' })
        },
      })
    } catch {
      Taro.showToast({ title: '海报生成异常', icon: 'none' })
    }
  }, [metrics])

  /* ---- 下拉刷新 ---- */
  const onRefresh = useCallback(() => {
    loadAll()
    if (activeTab === 'products') loadProducts()
    if (activeTab === 'promoters') loadPromoters()
    if (activeTab === 'details') loadDetails()
  }, [activeTab, loadAll, loadProducts, loadPromoters, loadDetails])

  /* ================================================================ */
  /*  渲染                                                             */
  /* ================================================================ */

  /* --- Loading --- */
  if (loading && !metrics) {
    return (
      <View className='promoter'>
        <View className='promoter__loading'>
          {[1, 2, 3, 4].map((i) => (
            <View key={i} className='promoter__skeleton-card' />
          ))}
        </View>
      </View>
    )
  }

  /* --- Error --- */
  if (error && !metrics) {
    return (
      <View className='promoter'>
        <View className='promoter__error'>
          <Text className='promoter__error-icon'>😵</Text>
          <Text className='promoter__error-msg'>{error}</Text>
          <Button className='promoter__error-btn' onClick={onRefresh}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  return (
    <View className='promoter'>
      <ScrollView
        className='promoter__scroll'
        scrollY
        enhanced
        showScrollbar={false}
        lowerThreshold={50}
      >
        {/* ================ 收益概览卡片 ================ */}
        <View className='promoter__overview'>
          <View className='promoter__overview-bg' />
          <View className='promoter__overview-content'>
            <Text className='promoter__overview-title'>收益概览</Text>
            <View className='promoter__overview-grid'>
              <View className='promoter__overview-item'>
                <Text className='promoter__overview-value'>
                  ¥{toYuan(metrics?.today_earnings ?? 0)}
                </Text>
                <Text className='promoter__overview-label'>今日收益</Text>
              </View>
              <View className='promoter__overview-item'>
                <Text className='promoter__overview-value'>
                  ¥{toYuan(metrics?.month_earnings ?? 0)}
                </Text>
                <Text className='promoter__overview-label'>本月收益</Text>
              </View>
              <View className='promoter__overview-item'>
                <Text className='promoter__overview-value'>
                  ¥{toYuan(metrics?.total_earnings ?? 0)}
                </Text>
                <Text className='promoter__overview-label'>总收益</Text>
              </View>
              <View className='promoter__overview-item'>
                <Text className='promoter__overview-value'>
                  {metrics?.order_count ?? 0}
                </Text>
                <Text className='promoter__overview-label'>推广订单</Text>
              </View>
            </View>
          </View>
        </View>

        {/* ================ 7日收益趋势 ================ */}
        <BarChart data={trends} />

        {/* ================ 推广码区域 ================ */}
        {metrics?.promo_code && (
          <View className='promoter__promo-code'>
            <View className='promoter__promo-code-header'>
              <Text className='promoter__promo-code-title'>我的推广码</Text>
            </View>
            <View className='promoter__promo-code-body'>
              <Text className='promoter__promo-code-value'>{metrics.promo_code}</Text>
              <Button
                className='promoter__promo-code-btn'
                onClick={() => {
                  Taro.setClipboardData({
                    data: metrics.promo_code,
                    success: () => {
                      Taro.showToast({ title: '推广码已复制', icon: 'success' })
                    },
                  })
                }}
              >
                复制推广码
              </Button>
            </View>
            <Button
              className='promoter__poster-btn'
              onClick={drawPoster}
            >
              生成推广海报
            </Button>
          </View>
        )}

        {/* 隐藏 Canvas（用于生成海报） */}
        <Canvas
          ref={canvasRef}
          className='promoter__canvas'
          canvasId='promoterPoster'
          style={{ width: '300px', height: '480px', position: 'absolute', left: '-9999px' }}
        />

        {/* ================ 团队简介 ================ */}
        {metrics && (
          <View className='promoter__team-summary'>
            <View className='promoter__team-summary-item'>
              <Text className='promoter__team-summary-value'>{metrics.team_size}</Text>
              <Text className='promoter__team-summary-label'>团队人数</Text>
            </View>
            <View className='promoter__team-summary-divider' />
            <View className='promoter__team-summary-item'>
              <Text className='promoter__team-summary-value'>
                ¥{toYuan(metrics.team_earnings)}
              </Text>
              <Text className='promoter__team-summary-label'>团队收益</Text>
            </View>
          </View>
        )}

        {/* ================ 内容区（底部 Tab 联动） ================ */}
        <View className='promoter__content'>
          {/* Tab 标题 */}
          <View className='promoter__tabs'>
            {TAB_ITEMS.map((tab) => (
              <View
                key={tab.key}
                className={`promoter__tab ${activeTab === tab.key ? 'promoter__tab--active' : ''}`}
                onClick={() => setActiveTab(tab.key)}
              >
                <Text className='promoter__tab-label'>{tab.label}</Text>
                {activeTab === tab.key && <View className='promoter__tab-indicator' />}
              </View>
            ))}
          </View>

          {/* 推广商品 Tab */}
          {activeTab === 'products' && (
            <View className='promoter__product-list'>
              {products.length === 0 ? (
                <View className='promoter__empty'>
                  <Text className='promoter__empty-icon'>📦</Text>
                  <Text className='promoter__empty-text'>暂无推广商品</Text>
                </View>
              ) : (
                products.map((product) => (
                  <View key={product.id} className='promoter__product-card'>
                    <View className='promoter__product-info'>
                      {product.cover_image && (
                        <Image
                          className='promoter__product-cover'
                          src={product.cover_image}
                          mode='aspectFill'
                        />
                      )}
                      <View className='promoter__product-meta'>
                        <Text className='promoter__product-name'>{product.name}</Text>
                        {product.description && (
                          <Text className='promoter__product-desc'>{product.description}</Text>
                        )}
                        <Text className='promoter__product-commission'>
                          佣金: ¥{toYuan(product.commission)}
                          {product.commission_rate > 0 &&
                            ` (${product.commission_rate.toFixed(1)}%)`}
                        </Text>
                        <Text className='promoter__product-sales'>
                          已售 {product.sales_count} 件
                        </Text>
                      </View>
                    </View>
                    <View className='promoter__product-actions'>
                      <Button
                        className='promoter__product-btn promoter__product-btn--copy'
                        onClick={() => copyLink(product)}
                      >
                        复制链接
                      </Button>
                      <Button
                        className='promoter__product-btn promoter__product-btn--share'
                        onClick={() => shareProduct(product)}
                      >
                        分享
                      </Button>
                    </View>
                  </View>
                ))
              )}
            </View>
          )}

          {/* 推广员 Tab */}
          {activeTab === 'promoters' && (
            <View className='promoter__promoter-list'>
              {promoters.length === 0 ? (
                <View className='promoter__empty'>
                  <Text className='promoter__empty-icon'>👥</Text>
                  <Text className='promoter__empty-text'>暂无下级推广员</Text>
                </View>
              ) : (
                promoters.map((p) => (
                  <View key={p.id} className='promoter__promoter-card'>
                    <Image
                      className='promoter__promoter-avatar'
                      src={p.avatar || PLACEHOLDER.avatar64}
                      mode='aspectFill'
                    />
                    <View className='promoter__promoter-info'>
                      <Text className='promoter__promoter-name'>{p.nickname}</Text>
                      <Text className='promoter__promoter-stats'>
                        {p.order_count} 单 · 活跃 {p.active_days} 天
                      </Text>
                    </View>
                    <Text className='promoter__promoter-earnings'>
                      ¥{toYuan(p.earnings)}
                    </Text>
                  </View>
                ))
              )}
            </View>
          )}

          {/* 收益明细 Tab */}
          {activeTab === 'details' && (
            <View className='promoter__detail-list'>
              {details.length === 0 ? (
                <View className='promoter__empty'>
                  <Text className='promoter__empty-icon'>💰</Text>
                  <Text className='promoter__empty-text'>暂无收益记录</Text>
                </View>
              ) : (
                details.map((d) => (
                  <View key={d.id} className='promoter__detail-card'>
                    <View className='promoter__detail-left'>
                      <Text className='promoter__detail-type'>
                        {d.type === 'commission'
                          ? '佣金'
                          : d.type === 'team_bonus'
                            ? '团队分红'
                            : '提现'}
                      </Text>
                      {d.product_name && (
                        <Text className='promoter__detail-product'>{d.product_name}</Text>
                      )}
                      <Text className='promoter__detail-date'>
                        {d.created_at?.slice(0, 10) ?? ''}
                      </Text>
                    </View>
                    <View className='promoter__detail-right'>
                      <Text
                        className={`promoter__detail-amount ${d.type === 'withdraw' ? 'promoter__detail-amount--out' : ''}`}
                      >
                        {d.type === 'withdraw' ? '-' : '+'}¥{toYuan(d.amount)}
                      </Text>
                      <Text
                        className={`promoter__detail-status promoter__detail-status--${d.status}`}
                      >
                        {d.status === 'settled' ? '已结算' : d.status === 'pending' ? '待结算' : '失败'}
                      </Text>
                    </View>
                  </View>
                ))
              )}
            </View>
          )}
        </View>

        {/* 底部间距 */}
        <View className='promoter__bottom-spacer' />
      </ScrollView>
    </View>
  )
}

export default Promoter
