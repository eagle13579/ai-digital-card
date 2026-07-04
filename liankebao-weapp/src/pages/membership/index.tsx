import { FC, useState, useEffect, useCallback } from 'react'
import { View, Text, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { pricingApi, paymentApi } from '../../api/digitalBrochure'
import './index.scss'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

type PageStatus = 'loading' | 'ready' | 'error'

interface PlanItem {
  id: string
  name: string
  label: string
  price_month: number
  price_year: number
  benefits: string[]
  /** 是否为当前套餐 */
  current?: boolean
}

interface UsageItem {
  key: string
  label: string
  used: number
  total: number
}

/* ========================================================================== */
/*  常量 — 会员等级与权益                                                        */
/* ========================================================================== */

const DEFAULT_PLANS: PlanItem[] = [
  {
    id: 'free',
    name: '免费版',
    label: 'Free',
    price_month: 0,
    price_year: 0,
    benefits: ['5 张数字名片', '每日 10 次匹配', '5 次 AI 聊天/天', '不支持 NFC 写入', '基础模板'],
  },
  {
    id: 'pro',
    name: '专业版',
    label: 'Pro',
    price_month: 99,
    price_year: 990,
    benefits: ['50 张数字名片', '每日 100 次匹配', '50 次 AI 聊天/天', '支持 NFC 写入', '全部高级模板', '去除水印'],
  },
  {
    id: 'enterprise',
    name: '企业版',
    label: 'Enterprise',
    price_month: 499,
    price_year: 4990,
    benefits: ['无限名片', '无限匹配', '无限 AI 聊天', '支持 NFC 写入', '全部高级模板', '团队管理', '专属客服', 'API 接入'],
  },
]

/** 等级徽章颜色映射 */
const LEVEL_COLORS: Record<string, string> = {
  free: '#8c8c8c',
  pro: '#1677ff',
  enterprise: '#722ed1',
}

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Membership: FC = () => {
  /* ---- 状态 ---- */
  const [status, setStatus] = useState<PageStatus>('loading')
  const [errorMsg, setErrorMsg] = useState('')
  const [plans, setPlans] = useState<PlanItem[]>(DEFAULT_PLANS)
  const [currentPlanId, setCurrentPlanId] = useState<string>('free')
  const [usageList, setUsageList] = useState<UsageItem[]>([])
  const [upgrading, setUpgrading] = useState(false)

  /* ---- 加载套餐与用量 ---- */
  const loadData = useCallback(async () => {
    setStatus('loading')
    setErrorMsg('')
    try {
      const [planRes, usageRes] = await Promise.all([pricingApi.getPlans(), pricingApi.getUsage()])

      // 处理套餐数据
      if (planRes.code === 200 || planRes.code === 0) {
        const remotePlans = (planRes.data as any)?.plans ?? []
        if (remotePlans.length > 0) {
          setPlans(remotePlans)
          const active = remotePlans.find((p: any) => p.current) as PlanItem | undefined
          if (active) setCurrentPlanId(active.id)
        }
      }

      // 处理用量数据
      if (usageRes.code === 200 || usageRes.code === 0) {
        const usageData = (usageRes.data as any)?.items ?? []
        setUsageList(usageData)
      }

      setStatus('ready')
    } catch (e: any) {
      setErrorMsg(e.message || '加载失败')
      setStatus('error')
    }
  }, [])

  useEffect(() => {
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* ---- 升级套餐 ---- */
  const handleUpgrade = useCallback(
    async (plan: PlanItem) => {
      if (plan.id === currentPlanId || plan.price_month === 0) return
      if (plan.id === 'free') return

      setUpgrading(true)
      try {
        // 先调用 upgrade 获取订单号
        const upgradeRes = await pricingApi.upgrade(plan.id, { period: 'month' })
        if (upgradeRes.code === 200 || upgradeRes.code === 0) {
          const orderNo = (upgradeRes.data as any)?.order_no
          if (orderNo) {
            const payRes = await paymentApi.wxPay(orderNo)
            if (payRes.code === 200 || payRes.code === 0) {
              Taro.showToast({ title: '升级成功', icon: 'success' })
              loadData()
            } else {
              Taro.showToast({ title: payRes.message || '支付失败', icon: 'none' })
            }
          }
        } else {
          Taro.showToast({ title: upgradeRes.message || '升级失败', icon: 'none' })
        }
      } catch (e: any) {
        Taro.showToast({ title: e.message || '操作失败', icon: 'none' })
      } finally {
        setUpgrading(false)
      }
    },
    [currentPlanId, loadData],
  )

  /* ---- 下拉刷新 ---- */
  const onRefresh = useCallback(() => {
    loadData()
  }, [loadData])

  /* ================================================================ */
  /*  渲染：各状态                                                      */
  /* ================================================================ */

  if (status === 'loading') {
    return (
      <View className='membership'>
        <View className='membership__skeleton'>
          <View className='membership__skeleton-header' />
          <View className='membership__skeleton-card' />
          <View className='membership__skeleton-card' />
          <View className='membership__skeleton-card' />
          <View className='membership__skeleton-usage' />
        </View>
      </View>
    )
  }

  if (status === 'error') {
    return (
      <View className='membership'>
        <View className='membership__error'>
          <Text className='membership__error-icon'>😵</Text>
          <Text className='membership__error-title'>加载失败</Text>
          <Text className='membership__error-message'>{errorMsg || '请检查网络后重试'}</Text>
          <Button className='membership__error-btn' onClick={onRefresh}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  return (
    <View className='membership'>
      <ScrollView className='membership__scroll' scrollY enhanced showScrollbar={false}>
        {/* ================ 当前会员等级 ================ */}
        <View className='membership__level-header'>
          <View
            className='membership__level-badge'
            style={{ background: LEVEL_COLORS[currentPlanId] || '#8c8c8c' }}
          >
            <Text className='membership__level-icon'>
              {currentPlanId === 'enterprise' ? '🏢' : currentPlanId === 'pro' ? '⭐' : '🆓'}
            </Text>
            <Text className='membership__level-name'>
              {plans.find((p) => p.id === currentPlanId)?.name || '免费版'}
            </Text>
          </View>
          <Text className='membership__level-desc'>畅享更多权益，提升商务效率</Text>
        </View>

        {/* ================ 定价卡片 ================ */}
        <View className='membership__plans'>
          {plans.map((plan) => {
            const isCurrent = plan.id === currentPlanId
            const isFree = plan.id === 'free'
            const monthlyDisplay = isFree ? '0' : `¥${plan.price_month}`
            const yearlyMonthly = isFree ? '0' : `¥${Math.round(plan.price_year / 12)}`
            const hasDiscount = !isFree && plan.price_year < plan.price_month * 12

            return (
              <View
                key={plan.id}
                className={`membership__plan-card ${isCurrent ? 'membership__plan-card--current' : ''} ${
                  plan.id === 'enterprise' ? 'membership__plan-card--enterprise' : ''
                }`}
              >
                {/* 年付折扣标签 */}
                {hasDiscount && (
                  <View className='membership__plan-tag'>
                    <Text className='membership__plan-tag-text'>
                      年付 ¥{plan.price_year}（省 ¥{plan.price_month * 12 - plan.price_year}）
                    </Text>
                  </View>
                )}

                <View className='membership__plan-header'>
                  <Text className='membership__plan-name'>{plan.name}</Text>
                  <Text className='membership__plan-label'>{plan.label}</Text>
                </View>

                <View className='membership__plan-price'>
                  <Text className='membership__plan-price-value'>{monthlyDisplay}</Text>
                  {!isFree && <Text className='membership__plan-price-unit'>/月</Text>}
                </View>

                {hasDiscount && (
                  <Text className='membership__plan-yearly'>
                    年付平均 {yearlyMonthly}/月
                  </Text>
                )}

                {/* 权益列表 */}
                <View className='membership__plan-benefits'>
                  {plan.benefits.map((benefit, idx) => (
                    <View key={idx} className='membership__plan-benefit'>
                      <Text className='membership__plan-benefit-icon'>✓</Text>
                      <Text className='membership__plan-benefit-text'>{benefit}</Text>
                    </View>
                  ))}
                </View>

                {/* 操作按钮 */}
                {isCurrent ? (
                  <View className='membership__plan-btn membership__plan-btn--current'>
                    <Text className='membership__plan-btn-text'>当前套餐</Text>
                  </View>
                ) : isFree ? (
                  <View
                    className='membership__plan-btn membership__plan-btn--free'
                    onClick={() =>
                      Taro.showToast({ title: '当前已是免费版', icon: 'none' })
                    }
                  >
                    <Text className='membership__plan-btn-text'>降级至免费版</Text>
                  </View>
                ) : (
                  <Button
                    className='membership__plan-btn membership__plan-btn--upgrade'
                    loading={upgrading}
                    onClick={() => handleUpgrade(plan)}
                  >
                    <Text className='membership__plan-btn-text'>
                      {currentPlanId === 'free' ? '立即升级' : '切换套餐'}
                    </Text>
                  </Button>
                )}
              </View>
            )
          })}
        </View>

        {/* ================ 用量进度 ================ */}
        {usageList.length > 0 && (
          <View className='membership__usage'>
            <Text className='membership__usage-title'>📊 当前用量</Text>
            {usageList.map((item) => {
              const percent = item.total > 0 ? Math.min((item.used / item.total) * 100, 100) : 0
              const isNearLimit = percent >= 80
              const isOverLimit = percent >= 100

              return (
                <View key={item.key} className='membership__usage-item'>
                  <View className='membership__usage-header'>
                    <Text className='membership__usage-label'>{item.label}</Text>
                    <Text
                      className={`membership__usage-count ${
                        isOverLimit
                          ? 'membership__usage-count--over'
                          : isNearLimit
                          ? 'membership__usage-count--warn'
                          : ''
                      }`}
                    >
                      {item.used} / {item.total}
                    </Text>
                  </View>
                  <View className='membership__usage-bar'>
                    <View
                      className={`membership__usage-bar-fill ${
                        isOverLimit
                          ? 'membership__usage-bar-fill--over'
                          : isNearLimit
                          ? 'membership__usage-bar-fill--warn'
                          : ''
                      }`}
                      style={{ width: `${Math.min(percent, 100)}%` }}
                    />
                  </View>
                </View>
              )
            })}
          </View>
        )}

        {/* 底部间距 */}
        <View className='membership__bottom-spacer' />
      </ScrollView>
    </View>
  )
}

export default Membership
