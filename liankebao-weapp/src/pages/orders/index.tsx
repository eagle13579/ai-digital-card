import { FC, useState, useEffect, useCallback } from 'react'
import { View, Text, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import paymentApi, { OrderItem } from '../../api/payment'
import './index.scss'

/* ========================================================================== */
/*  类型与常量                                                                  */
/* ========================================================================== */

type TabKey = 'all' | 'pending' | 'paid' | 'completed' | 'cancelled'
type PageStatus = 'loading' | 'ready' | 'error'

interface TabItem {
  key: TabKey
  label: string
}

const TABS: TabItem[] = [
  { key: 'all', label: '全部' },
  { key: 'pending', label: '待付款' },
  { key: 'paid', label: '已付款' },
  { key: 'completed', label: '已完成' },
  { key: 'cancelled', label: '已取消' },
]

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending: { label: '待付款', color: '#fa8c16' },
  paid: { label: '已付款', color: '#52c41a' },
  completed: { label: '已完成', color: '#1677ff' },
  cancelled: { label: '已取消', color: '#999' },
}

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Orders: FC = () => {
  /* ---- 状态 ---- */
  const [status, setStatus] = useState<PageStatus>('loading')
  const [orders, setOrders] = useState<OrderItem[]>([])
  const [activeTab, setActiveTab] = useState<TabKey>('all')
  const [errorMsg, setErrorMsg] = useState('')
  const [payingId, setPayingId] = useState<string | null>(null)

  /* ---- 加载订单列表 ---- */
  const loadOrders = useCallback(async (tab: TabKey) => {
    setStatus('loading')
    setErrorMsg('')
    try {
      const params: any = { page: 1, page_size: 50 }
      if (tab !== 'all') {
        params.status = tab
      }
      const res = await paymentApi.getOrders(params)
      if (res.code === 200 || res.code === 0) {
        const data = res.data as any
        const list: OrderItem[] = data?.list ?? data ?? []
        setOrders(list)
        setStatus('ready')
      } else {
        setErrorMsg(res.message || '加载失败')
        setStatus('error')
      }
    } catch (e: any) {
      setErrorMsg(e.message || '加载订单失败')
      setStatus('error')
    }
  }, [])

  /* ---- 初始化 ---- */
  useEffect(() => {
    loadOrders(activeTab)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  /* ---- 切换 Tab ---- */
  const switchTab = useCallback((key: TabKey) => {
    setActiveTab(key)
  }, [])

  /* ---- 去支付 ---- */
  const handlePay = useCallback(async (order: OrderItem) => {
    setPayingId(order.id)
    try {
      const res = await paymentApi.wxPay(order.id)
      if (res.code === 200 || res.code === 0) {
        const data = res.data as any
        const payParams = data?.payParams ?? {}
        // 调起微信支付
        const payRes = await Taro.requestPayment({
          timeStamp: payParams.timeStamp,
          nonceStr: payParams.nonceStr,
          package: payParams.package,
          signType: payParams.signType || 'MD5',
          paySign: payParams.paySign,
        })
        if (payRes.errMsg === 'requestPayment:ok') {
          Taro.showToast({ title: '支付成功', icon: 'success' })
          // 刷新订单列表
          loadOrders(activeTab)
        } else {
          Taro.showToast({ title: '支付取消', icon: 'none' })
        }
      } else {
        Taro.showToast({ title: res.message || '支付失败', icon: 'none' })
      }
    } catch (e: any) {
      Taro.showToast({ title: e.message || '支付失败', icon: 'none' })
    } finally {
      setPayingId(null)
    }
  }, [activeTab, loadOrders])

  /* ---- 再次购买 ---- */
  const handleRebuy = useCallback((order: OrderItem) => {
    if (order.product_id) {
      Taro.navigateTo({
        url: `/pages/product/detail/index?id=${order.product_id}`,
      })
    } else {
      Taro.showToast({ title: '商品信息已失效', icon: 'none' })
    }
  }, [])

  /* ---- 下拉刷新 ---- */
  const onRefresh = useCallback(() => {
    loadOrders(activeTab)
  }, [activeTab, loadOrders])

  /* ---- 格式化金额 ---- */
  const formatAmount = (amount: number): string => {
    return `¥${(amount / 100).toFixed(2)}`
  }

  /* ---- 格式化时间 ---- */
  const formatTime = (timeStr: string): string => {
    if (!timeStr) return ''
    // 取前 16 字符: YYYY-MM-DD HH:mm
    return timeStr.slice(0, 16).replace('T', ' ')
  }

  /* ---- 获取订单状态信息 ---- */
  const getStatusInfo = (order: OrderItem) => {
    return STATUS_MAP[order.status] || { label: order.status, color: '#999' }
  }

  /* ================================================================ */
  /*  渲染                                                              */
  /* ================================================================ */

  /* --- Loading 骨架屏 --- */
  if (status === 'loading') {
    return (
      <View className='orders'>
        <View className='orders__tabs'>
          {TABS.map((tab) => (
            <View
              key={tab.key}
              className={`orders__tab ${activeTab === tab.key ? 'orders__tab--active' : ''}`}
              onClick={() => switchTab(tab.key)}
            >
              <Text className='orders__tab-label'>{tab.label}</Text>
            </View>
          ))}
        </View>
        <View className='orders__skeleton'>
          {[1, 2, 3].map((i) => (
            <View key={i} className='orders__skeleton-card'>
              <View className='orders__skeleton-line orders__skeleton-line--wide' />
              <View className='orders__skeleton-line orders__skeleton-line--narrow' />
              <View className='orders__skeleton-line orders__skeleton-line--medium' />
            </View>
          ))}
        </View>
      </View>
    )
  }

  /* --- 错误状态 --- */
  if (status === 'error') {
    return (
      <View className='orders'>
        <View className='orders__tabs'>
          {TABS.map((tab) => (
            <View
              key={tab.key}
              className={`orders__tab ${activeTab === tab.key ? 'orders__tab--active' : ''}`}
              onClick={() => switchTab(tab.key)}
            >
              <Text className='orders__tab-label'>{tab.label}</Text>
            </View>
          ))}
        </View>
        <View className='orders__error'>
          <Text className='orders__error-icon'>😵</Text>
          <Text className='orders__error-title'>加载失败</Text>
          <Text className='orders__error-message'>{errorMsg || '请检查网络后重试'}</Text>
          <Button className='orders__error-btn' onClick={onRefresh}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  return (
    <View className='orders'>
      {/* ================ Tab 栏 ================ */}
      <View className='orders__tabs'>
        <ScrollView className='orders__tabs-scroll' scrollX enhanced showScrollbar={false}>
          {TABS.map((tab) => (
            <View
              key={tab.key}
              className={`orders__tab ${activeTab === tab.key ? 'orders__tab--active' : ''}`}
              onClick={() => switchTab(tab.key)}
            >
              <Text className='orders__tab-label'>{tab.label}</Text>
            </View>
          ))}
        </ScrollView>
      </View>

      <ScrollView
        className='orders__scroll'
        scrollY
        enhanced
        showScrollbar={false}
        lowerThreshold={50}
        refresherEnabled
        refresherTriggered={false}
        onRefresherRefresh={onRefresh}
      >
        {/* ================ 订单列表 ================ */}
        {orders.length > 0 ? (
          <View className='orders__list'>
            {orders.map((order) => {
              const statusInfo = getStatusInfo(order)
              return (
                <View key={order.id} className='orders__card'>
                  {/* 订单头部: 订单号 + 状态 */}
                  <View className='orders__card-header'>
                    <Text className='orders__order-no'>
                      订单号: {order.order_no || order.id.slice(0, 12)}
                    </Text>
                    <Text
                      className='orders__order-status'
                      style={{ color: statusInfo.color }}
                    >
                      {statusInfo.label}
                    </Text>
                  </View>

                  {/* 订单内容 */}
                  <View className='orders__card-body'>
                    <View className='orders__card-info'>
                      <Text className='orders__product-name'>
                        {order.product_name || '商品名称'}
                      </Text>
                      <Text className='orders__order-time'>
                        {formatTime(order.created_at)}
                      </Text>
                    </View>
                    <Text className='orders__amount'>
                      {formatAmount(order.amount)}
                    </Text>
                  </View>

                  {/* 操作按钮 */}
                  <View className='orders__card-actions'>
                    {order.status === 'pending' && (
                      <Button
                        className='orders__action-btn orders__action-btn--pay'
                        onClick={() => handlePay(order)}
                        loading={payingId === order.id}
                        disabled={payingId === order.id}
                      >
                        去支付
                      </Button>
                    )}
                    {order.status === 'completed' && (
                      <Button
                        className='orders__action-btn orders__action-btn--rebuy'
                        onClick={() => handleRebuy(order)}
                      >
                        再次购买
                      </Button>
                    )}
                    {order.status === 'paid' && (
                      <Text className='orders__action-hint'>等待处理</Text>
                    )}
                    {order.status === 'cancelled' && (
                      <Text className='orders__action-hint'>已取消</Text>
                    )}
                  </View>
                </View>
              )
            })}
          </View>
        ) : (
          /* --- 空状态 --- */
          <View className='orders__empty'>
            <Text className='orders__empty-icon'>📋</Text>
            <Text className='orders__empty-title'>暂无订单</Text>
            <Text className='orders__empty-desc'>快去逛逛发现好商品吧</Text>
          </View>
        )}

        {/* 底部间距 */}
        <View className='orders__bottom-spacer' />
      </ScrollView>
    </View>
  )
}

export default Orders
