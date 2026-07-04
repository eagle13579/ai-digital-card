import { FC, useState, useCallback, useMemo } from 'react'
import { View, Text, Image, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import './index.scss'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

interface ActivityItem {
  id: string
  title: string
  startTime: string
  endTime: string
  cover?: string
  location?: string
  organizer?: string
  description: string
  tags?: string[]
  status: 'ongoing' | 'ended'
  url?: string
}

/* ========================================================================== */
/*  Demo 数据 — 活动列表                                                       */
/* ========================================================================== */

const DEMO_ACTIVITIES: ActivityItem[] = [
  {
    id: 'a_1',
    title: '2025 链客AI名片产品发布会',
    startTime: '2025-03-15 14:00',
    endTime: '2025-03-15 17:00',
    cover: PLACEHOLDER.cover280x160,
    location: '北京 · 国家会议中心',
    organizer: '链客科技',
    description:
      '链客科技全新AI数字名片产品发布，诚邀各界合作伙伴莅临品鉴。现场将展示最新的AI名片功能与智能匹配引擎。',
    tags: ['发布会', 'AI', '名片'],
    status: 'ended',
  },
  {
    id: 'a_2',
    title: 'AI商业匹配沙龙 · 上海站',
    startTime: '2025-04-20 14:00',
    endTime: '2025-04-20 18:00',
    cover: PLACEHOLDER.cover280x160,
    location: '上海 · 浦东新区',
    organizer: '链客科技',
    description:
      '线下AI商业匹配沙龙，邀请各行业企业家、创业者面对面交流。现场AI智能匹配，高效对接合作资源。',
    tags: ['沙龙', 'AI匹配', '线下交流'],
    status: 'ended',
  },
  {
    id: 'a_3',
    title: '数字营销实战线上分享会',
    startTime: '2025-05-10 19:30',
    endTime: '2025-05-10 21:00',
    cover: PLACEHOLDER.cover280x160,
    location: '线上 · 腾讯会议',
    organizer: '链客科技 · 市场部',
    description:
      '特邀行业专家分享2025年数字营销趋势与实战案例，涵盖私域运营、短视频获客、AI营销工具等热点话题。',
    tags: ['线上', '营销', '分享'],
    status: 'ended',
  },
  {
    id: 'a_4',
    title: '链客生态合作伙伴大会 2025',
    startTime: '2025-06-01 09:00',
    endTime: '2025-06-02 18:00',
    cover: PLACEHOLDER.cover280x160,
    location: '深圳 · 会展中心',
    organizer: '链客科技',
    description:
      '汇聚链客生态各领域合作伙伴，共同探讨AI技术与商业融合的未来。大会设有主论坛、分论坛及展区交流环节。',
    tags: ['大会', '生态', '合作'],
    status: 'ended',
  },
  {
    id: 'a_5',
    title: 'AI名片使用技巧在线培训（7月）',
    startTime: '2025-07-12 15:00',
    endTime: '2025-07-12 16:30',
    cover: PLACEHOLDER.cover280x160,
    location: '线上 · 链客直播间',
    organizer: '链客科技 · 客户成功部',
    description:
      '手把手教您使用AI名片各项功能，包括创建、分享、匹配、推广等，助您快速上手并最大化利用平台资源。',
    tags: ['培训', '线上', '入门'],
    status: 'ongoing',
    url: 'https://example.com/live/7',
  },
  {
    id: 'a_6',
    title: '供需对接会 · 京津冀专场',
    startTime: '2025-07-25 14:00',
    endTime: '2025-07-25 17:30',
    cover: PLACEHOLDER.cover280x160,
    location: '天津 · 滨海新区',
    organizer: '链客科技 · 华北运营中心',
    description:
      '聚焦京津冀地区的供需对接活动，涵盖科技、制造、服务等行业，现场匹配+自由交流，高效促成合作。',
    tags: ['供需', '对接', '京津冀'],
    status: 'ongoing',
  },
  {
    id: 'a_7',
    title: 'AI赋能中小企业数字化转型论坛',
    startTime: '2025-08-08 09:30',
    endTime: '2025-08-08 17:00',
    cover: PLACEHOLDER.cover280x160,
    location: '成都 · 世纪城国际会展中心',
    organizer: '链客科技 · 西南运营中心',
    description:
      '论坛聚焦AI技术如何赋能中小企业实现数字化转型，邀请多位行业专家、企业家分享实践经验与应用案例。',
    tags: ['论坛', '数字化', 'AI'],
    status: 'ongoing',
  },
]

/* ========================================================================== */
/*  状态筛选选项                                                               */
/* ========================================================================== */

const STATUS_FILTERS = [
  { key: 'all', label: '全部' },
  { key: 'ongoing', label: '进行中' },
  { key: 'ended', label: '已结束' },
]

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Activities: FC = () => {
  /* ---- 状态 ---- */
  const [statusFilter, setStatusFilter] = useState<'all' | 'ongoing' | 'ended'>('all')

  /* ---- 筛选 ---- */
  const filtered = useMemo(() => {
    if (statusFilter === 'all') return DEMO_ACTIVITIES
    return DEMO_ACTIVITIES.filter((a) => a.status === statusFilter)
  }, [statusFilter])

  /* ---- 切换筛选 ---- */
  const switchFilter = useCallback((key: 'all' | 'ongoing' | 'ended') => {
    setStatusFilter(key)
  }, [])

  /* ---- 报名 / 查看活动 ---- */
  const handleAction = useCallback((activity: ActivityItem) => {
    if (activity.status === 'ongoing') {
      // 进行中的活动跳转详情/报名
      Taro.showModal({
        title: '报名确认',
        content: `确认报名「${activity.title}」？`,
        success: (res) => {
          if (res.confirm) {
            Taro.showToast({ title: '报名成功', icon: 'success' })
          }
        },
      })
    } else {
      // 已结束的活动显示详情
      Taro.showToast({
        title: activity.description.slice(0, 30) + '...',
        icon: 'none',
        duration: 2000,
      })
    }
  }, [])

  /* ---- 格式化日期显示 ---- */
  const formatDate = (dateStr: string) => {
    // 显示 MM/DD HH:mm 格式
    const parts = dateStr.split(' ')
    if (parts.length === 2) {
      const datePart = parts[0].split('-')
      if (datePart.length === 3) {
        return `${datePart[1]}/${datePart[2]} ${parts[1].slice(0, 5)}`
      }
    }
    return dateStr
  }

  /* ---- 计算活动状态标签 ---- */
  const getStatusTag = (status: string) => {
    if (status === 'ongoing') {
      return { label: '进行中', className: 'activities__status-tag--ongoing' }
    }
    return { label: '已结束', className: 'activities__status-tag--ended' }
  }

  /* ================================================================ */
  /*  渲染                                                                  */
  /* ================================================================ */

  return (
    <View className='activities'>
      {/* ================ 页面标题 ================ */}
      <View className='activities__header'>
        <Text className='activities__header-title'>🎉 活动中心</Text>
        <Text className='activities__header-desc'>
          发现精彩活动，拓展商业人脉
        </Text>
      </View>

      {/* ================ 状态筛选 ================ */}
      <View className='activities__filters'>
        {STATUS_FILTERS.map((f) => (
          <View
            key={f.key}
            className={`activities__filter-tab ${statusFilter === f.key ? 'activities__filter-tab--active' : ''}`}
            onClick={() => switchFilter(f.key as 'all' | 'ongoing' | 'ended')}
          >
            <Text className='activities__filter-label'>{f.label}</Text>
          </View>
        ))}
      </View>

      {/* ================ 活动统计 ================ */}
      {statusFilter !== 'all' && (
        <View className='activities__stats'>
          <Text className='activities__stats-text'>
            {statusFilter === 'ongoing' ? '进行中' : '已结束'}活动{' '}
            {filtered.length} 个
          </Text>
        </View>
      )}

      {/* ================ 活动列表 ================ */}
      <ScrollView
        className='activities__scroll'
        scrollY
        enhanced
        showScrollbar={false}
        lowerThreshold={50}
      >
        {filtered.length > 0 ? (
          <View className='activities__list'>
            {filtered.map((activity) => {
              const statusTag = getStatusTag(activity.status)

              return (
                <View key={activity.id} className='activities__card'>
                  {/* 封面 */}
                  {activity.cover && (
                    <View className='activities__card-cover-wrap'>
                      <Image
                        className='activities__card-cover'
                        src={activity.cover}
                        mode='aspectFill'
                      />
                      {/* 状态标签叠加 */}
                      <View
                        className={`activities__status-tag ${statusTag.className}`}
                      >
                        <Text className='activities__status-dot' />
                        <Text className='activities__status-label'>
                          {statusTag.label}
                        </Text>
                      </View>
                    </View>
                  )}

                  {/* 活动信息 */}
                  <View className='activities__card-body'>
                    <Text className='activities__card-title'>
                      {activity.title}
                    </Text>

                    {/* 时间 */}
                    <View className='activities__card-meta'>
                      <Text className='activities__meta-icon'>🕐</Text>
                      <Text className='activities__meta-text'>
                        {formatDate(activity.startTime)}
                        {' ~ '}
                        {formatDate(activity.endTime)}
                      </Text>
                    </View>

                    {/* 地点 */}
                    {activity.location && (
                      <View className='activities__card-meta'>
                        <Text className='activities__meta-icon'>📍</Text>
                        <Text className='activities__meta-text'>
                          {activity.location}
                        </Text>
                      </View>
                    )}

                    {/* 主办方 */}
                    {activity.organizer && (
                      <View className='activities__card-meta'>
                        <Text className='activities__meta-icon'>🏢</Text>
                        <Text className='activities__meta-text'>
                          {activity.organizer}
                        </Text>
                      </View>
                    )}

                    {/* 描述 */}
                    <Text className='activities__card-desc' numberOfLines={2}>
                      {activity.description}
                    </Text>

                    {/* 标签 */}
                    {activity.tags && activity.tags.length > 0 && (
                      <View className='activities__card-tags'>
                        {activity.tags.map((tag) => (
                          <Text key={tag} className='activities__card-tag'>
                            {tag}
                          </Text>
                        ))}
                      </View>
                    )}

                    {/* 操作按钮 */}
                    <Button
                      className={`activities__card-btn ${
                        activity.status === 'ongoing'
                          ? 'activities__card-btn--primary'
                          : 'activities__card-btn--disabled'
                      }`}
                      onClick={() => handleAction(activity)}
                    >
                      {activity.status === 'ongoing' ? '立即报名' : '查看详情'}
                    </Button>
                  </View>
                </View>
              )
            })}
          </View>
        ) : (
          <View className='activities__empty'>
            <Text className='activities__empty-icon'>🎉</Text>
            <Text className='activities__empty-title'>暂无活动</Text>
            <Text className='activities__empty-desc'>
              {statusFilter === 'ongoing'
                ? '当前没有进行中的活动，请留意后续更新'
                : '当前没有已结束的活动'}
            </Text>
          </View>
        )}

        <View className='activities__bottom-spacer' />
      </ScrollView>
    </View>
  )
}

export default Activities
