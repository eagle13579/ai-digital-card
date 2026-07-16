/**
 * 平台详情页
 *
 * 三个Tab:
 *  1. 介绍 — 创建人信息 + 平台描述
 *  2. 资源单位 — 成员列表 (按角色排序)
 *  3. 平台商机 — 商业报告中的机会列表
 *
 * 状态: loading / error / ready
 * 功能: 加入平台 / 邀请弹窗 / 联系创建人
 */

import { FC, useState, useEffect, useCallback } from 'react'
import { View, Text, Button, ScrollView, Image } from '@tarojs/components'
import Taro from '@tarojs/taro'
import platformApi, { Platform, PlatformMember, PlatformReport } from '../../api/platform'
import './index.scss'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

type PageStatus = 'loading' | 'ready' | 'error'

type TabKey = 'info' | 'resources' | 'opportunities'

interface TabItem {
  key: TabKey
  label: string
}

/* ========================================================================== */
/*  常量                                                                       */
/* ========================================================================== */

const TABS: TabItem[] = [
  { key: 'info', label: '介绍' },
  { key: 'resources', label: '资源单位' },
  { key: 'opportunities', label: '平台商机' },
]

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const PlatformDetail: FC = () => {
  /* ---- 路由参数 ---- */
  const router = Taro.getCurrentInstance().router
  const platformId = Number(router?.params?.id) || 0

  /* ---- 状态 ---- */
  const [status, setStatus] = useState<PageStatus>('loading')
  const [activeTab, setActiveTab] = useState<TabKey>('info')
  const [platform, setPlatform] = useState<Platform | null>(null)
  const [members, setMembers] = useState<PlatformMember[]>([])
  const [report, setReport] = useState<PlatformReport | null>(null)
  const [alreadyJoined, setAlreadyJoined] = useState(false)
  const [joining, setJoining] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [showInviteModal, setShowInviteModal] = useState(false)

  /* ---- 获取当前 userId ---- */
  const getUserId = useCallback((): number | null => {
    const user = Taro.getStorageSync('user') || {}
    return user.id || null
  }, [])

  /* ---- 加载数据 ---- */
  const loadData = useCallback(async () => {
    if (!platformId) {
      setStatus('error')
      setErrorMsg('参数错误')
      return
    }

    setStatus('loading')
    setErrorMsg('')

    try {
      // 并发加载平台详情 + 成员列表
      const [platRes, membersRes] = await Promise.all([
        platformApi.getById(platformId),
        platformApi.getMembers(platformId),
      ])

      const plat = platRes.data as unknown as Platform
      if (!plat) {
        setStatus('error')
        setErrorMsg('平台不存在')
        return
      }

      const memberList = (membersRes.data as unknown as PlatformMember[]) || []
      const userId = getUserId()
      const isJoined = userId ? memberList.some((m) => m.user_id === userId) : false

      setPlatform(plat)
      setMembers(memberList)
      setAlreadyJoined(isJoined)

      // 尝试加载商业报告（仅秘书长可见，静默失败）
      try {
        const reportRes = await platformApi.getReport(platformId)
        setReport(reportRes.data as unknown as PlatformReport)
      } catch {
        // 非秘书长无权查看报告，不阻塞页面
      }

      setStatus('ready')
    } catch (e: any) {
      console.error('[PlatformDetail] 加载失败:', e)
      setStatus('error')
      setErrorMsg(e.message || '加载失败，请重试')
    }
  }, [platformId, getUserId])

  useEffect(() => {
    loadData()
  }, [loadData])

  /* ---- Tab 切换 ---- */
  const switchTab = useCallback((tab: TabKey) => {
    setActiveTab(tab)
  }, [])

  /* ---- 加入平台 ---- */
  const handleJoin = useCallback(async () => {
    if (joining || alreadyJoined || !platformId) return

    // 检查登录
    const token = Taro.getStorageSync('token')
    if (!token) {
      Taro.navigateTo({ url: '/pages/login/index' })
      return
    }

    setJoining(true)
    Taro.showLoading({ title: '加入中...' })

    try {
      await platformApi.join(platformId)
      Taro.hideLoading()
      Taro.showToast({ title: '加入成功', icon: 'success' })
      setAlreadyJoined(true)
      // 刷新页面
      loadData()
    } catch (e: any) {
      Taro.hideLoading()
      Taro.showToast({ title: e.message || '加入失败，请重试', icon: 'none' })
    } finally {
      setJoining(false)
    }
  }, [joining, alreadyJoined, platformId, loadData])

  /* ---- 邀请弹窗 ---- */
  const openInviteModal = useCallback(() => {
    setShowInviteModal(true)
  }, [])

  const closeInviteModal = useCallback(() => {
    setShowInviteModal(false)
  }, [])

  const inviteFromApp = useCallback(() => {
    Taro.showToast({ title: '选择询赋好友邀请', icon: 'none' })
    closeInviteModal()
  }, [closeInviteModal])

  const inviteFromWechat = useCallback(() => {
    Taro.showToast({ title: '选择微信好友邀请', icon: 'none' })
    closeInviteModal()
  }, [closeInviteModal])

  const showQRCode = useCallback(() => {
    Taro.showToast({ title: '展示平台二维码', icon: 'none' })
    closeInviteModal()
  }, [closeInviteModal])

  /* ---- 返回 ---- */
  const goBack = useCallback(() => {
    Taro.navigateBack()
  }, [])

  /* ====================================================================== */
  /*  渲染：加载骨架屏                                                        */
  /* ====================================================================== */

  if (status === 'loading') {
    return (
      <View className='platform-detail'>
        {/* 占位 header */}
        <View className='platform-detail__skeleton-header'>
          <View className='platform-detail__skeleton-back' />
          <View className='platform-detail__skeleton-invite' />
        </View>
        {/* 平台信息骨架 */}
        <View className='platform-detail__skeleton-hero'>
          <View className='platform-detail__skeleton-logo' />
          <View className='platform-detail__skeleton-info'>
            <View className='platform-detail__skeleton-line platform-detail__skeleton-line--name' />
            <View className='platform-detail__skeleton-line platform-detail__skeleton-line--desc' />
          </View>
        </View>
        {/* 统计栏骨架 */}
        <View className='platform-detail__skeleton-stats'>
          {[1, 2, 3, 4].map((i) => (
            <View key={i} className='platform-detail__skeleton-stat' />
          ))}
        </View>
        {/* Tab 骨架 */}
        <View className='platform-detail__skeleton-tabs'>
          {[1, 2, 3].map((i) => (
            <View key={i} className='platform-detail__skeleton-tab' />
          ))}
        </View>
        {/* 内容骨架 */}
        <View className='platform-detail__skeleton-content'>
          {[1, 2, 3, 4].map((i) => (
            <View key={i} className='platform-detail__skeleton-card'>
              <View className='platform-detail__skeleton-avatar' />
              <View className='platform-detail__skeleton-card-info'>
                <View className='platform-detail__skeleton-line platform-detail__skeleton-line--card-title' />
                <View className='platform-detail__skeleton-line platform-detail__skeleton-line--card-desc' />
              </View>
            </View>
          ))}
        </View>
      </View>
    )
  }

  /* ====================================================================== */
  /*  渲染：错误状态                                                          */
  /* ====================================================================== */

  if (status === 'error' || !platform) {
    return (
      <View className='platform-detail'>
        <View className='platform-detail__error'>
          <Text className='platform-detail__error-icon'>😵</Text>
          <Text className='platform-detail__error-title'>加载失败</Text>
          <Text className='platform-detail__error-msg'>{errorMsg || '请检查网络后重试'}</Text>
          <Button className='platform-detail__error-btn' onClick={loadData}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  /* ====================================================================== */
  /*  渲染：主内容                                                            */
  /* ====================================================================== */

  return (
    <View className='platform-detail'>
      {/* ================ 顶部导航栏 ================ */}
      <View className='platform-detail__header'>
        <View className='platform-detail__header-left' onClick={goBack}>
          <Text className='platform-detail__back-icon'>‹</Text>
        </View>
        <View className='platform-detail__header-title'>{platform.name}</View>
        <View className='platform-detail__header-right' onClick={openInviteModal}>
          <Text className='platform-detail__invite-btn'>+邀请</Text>
        </View>
      </View>

      {/* ================ 平台信息区 ================ */}
      <View className='platform-detail__hero'>
        <View className='platform-detail__logo'>
          <Text className='platform-detail__logo-text'>
            {platform.name ? platform.name[0] : 'P'}
          </Text>
        </View>
        <View className='platform-detail__hero-info'>
          <Text className='platform-detail__name'>{platform.name}</Text>
          <Text className='platform-detail__desc'>
            资源对接，请联系<Text className='platform-detail__secretary-link'>秘书处</Text>
          </Text>
        </View>
      </View>

      {/* ================ 统计栏 ================ */}
      <View className='platform-detail__stats'>
        <View className='platform-detail__stat-item'>
          <Text className='platform-detail__stat-num'>{platform.member_count || 0}</Text>
          <Text className='platform-detail__stat-label'>单位</Text>
        </View>
        <View className='platform-detail__stat-divider' />
        <View className='platform-detail__stat-item'>
          <Text className='platform-detail__stat-num'>{report?.total_members || 0}</Text>
          <Text className='platform-detail__stat-label'>商机</Text>
        </View>
        <View className='platform-detail__stat-divider' />
        <View className='platform-detail__stat-item'>
          <Text className='platform-detail__stat-num'>{report?.coverage?.industry_count || '--'}</Text>
          <Text className='platform-detail__stat-label'>行业</Text>
        </View>
        <View className='platform-detail__stat-divider' />
        <View className='platform-detail__stat-item'>
          <Text className='platform-detail__stat-num'>{report?.coverage?.company_count || '--'}</Text>
          <Text className='platform-detail__stat-label'>企业</Text>
        </View>
      </View>

      {/* ================ Tab 切换栏 ================ */}
      <View className='platform-detail__tabs'>
        {TABS.map((tab) => (
          <View
            key={tab.key}
            className={`platform-detail__tab ${activeTab === tab.key ? 'platform-detail__tab--active' : ''}`}
            onClick={() => switchTab(tab.key)}
          >
            <Text className='platform-detail__tab-label'>{tab.label}</Text>
            {activeTab === tab.key && <View className='platform-detail__tab-indicator' />}
          </View>
        ))}
      </View>

      {/* ================ Tab 内容区 ================ */}
      <ScrollView className='platform-detail__content' scrollY enhanced showScrollbar={false}>

        {/* --- Tab 1: 介绍 --- */}
        {activeTab === 'info' && (
          <View className='platform-detail__info'>
            {/* 创建人卡片 */}
            <View className='platform-detail__creator-card'>
              <View className='platform-detail__creator-avatar'>
                <Text className='platform-detail__avatar-text'>
                  {'?'}
                </Text>
              </View>
              <View className='platform-detail__creator-detail'>
                <Text className='platform-detail__creator-name'>
                  {report?.platform_name || platform.name} | 创建人
                </Text>
                <Text className='platform-detail__creator-meta'>
                  平台编号: {platform.platform_no || '--'}
                </Text>
              </View>
              <View className='platform-detail__creator-badge'>创建人</View>
            </View>

            {/* 平台描述 */}
            <View className='platform-detail__section'>
              <Text className='platform-detail__section-title'>平台介绍</Text>
              <Text className='platform-detail__section-content'>
                {platform.description || '暂无介绍'}
              </Text>
            </View>

            {/* 年费信息 */}
            <View className='platform-detail__section'>
              <Text className='platform-detail__section-title'>入会费用</Text>
              <Text className='platform-detail__section-content'>
                {platform.annual_fee > 0
                  ? `¥${platform.annual_fee} /年`
                  : '免费入驻'}
              </Text>
            </View>

            {/* 创建时间 */}
            {platform.created_at && (
              <View className='platform-detail__section'>
                <Text className='platform-detail__section-title'>创建时间</Text>
                <Text className='platform-detail__section-content'>
                  {new Date(platform.created_at).toLocaleDateString('zh-CN')}
                </Text>
              </View>
            )}

            {/* 资源单位预览 */}
            {members.length > 0 && (
              <View className='platform-detail__section'>
                <Text className='platform-detail__section-title'>
                  资源单位 ({members.length})
                </Text>
                <View className='platform-detail__unit-preview'>
                  {members.slice(0, 10).map((m) => (
                    <Text key={m.id} className='platform-detail__unit-tag'>
                      {m.name || m.company || '成员'}
                    </Text>
                  ))}
                  {members.length > 10 && (
                    <Text className='platform-detail__unit-tag platform-detail__unit-tag--more'>
                      +{members.length - 10}
                    </Text>
                  )}
                </View>
              </View>
            )}
          </View>
        )}

        {/* --- Tab 2: 资源单位 --- */}
        {activeTab === 'resources' && (
          <View className='platform-detail__resources'>
            {members.length > 0 ? (
              <View className='platform-detail__member-list'>
                {members.map((m) => (
                  <View key={m.id} className='platform-detail__member-card'>
                    <View className='platform-detail__member-avatar'>
                      {m.avatar ? (
                        <Image
                          className='platform-detail__member-avatar-img'
                          src={m.avatar}
                          mode='aspectFill'
                        />
                      ) : (
                        <Text className='platform-detail__member-avatar-text'>
                          {(m.name || '?')[0]}
                        </Text>
                      )}
                    </View>
                    <View className='platform-detail__member-info'>
                      <View className='platform-detail__member-top'>
                        <Text className='platform-detail__member-name' numberOfLines={1}>
                          {m.name}
                        </Text>
                        {m.role !== 'member' && (
                          <View className={`platform-detail__role-badge platform-detail__role-badge--${m.role}`}>
                            <Text className='platform-detail__role-text'>
                              {m.role === 'secretary_general' ? '秘书长' : '秘书处'}
                            </Text>
                          </View>
                        )}
                      </View>
                      <Text className='platform-detail__member-company'>
                        {[m.company, m.title].filter(Boolean).join(' · ') || '--'}
                      </Text>
                      <Text className='platform-detail__member-time'>
                        {m.joined_at
                          ? `加入于 ${new Date(m.joined_at).toLocaleDateString('zh-CN')}`
                          : ''}
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
            ) : (
              <View className='platform-detail__empty'>
                <Text className='platform-detail__empty-icon'>👥</Text>
                <Text className='platform-detail__empty-title'>暂无资源单位</Text>
                <Text className='platform-detail__empty-desc'>成员加入后将显示在这里</Text>
              </View>
            )}
          </View>
        )}

        {/* --- Tab 3: 平台商机 --- */}
        {activeTab === 'opportunities' && (
          <View className='platform-detail__opportunities'>
            {report ? (
              <View className='platform-detail__report-section'>
                {/* 统计概览 */}
                <View className='platform-detail__report-overview'>
                  <View className='platform-detail__report-card'>
                    <Text className='platform-detail__report-card-num'>{report.total_members}</Text>
                    <Text className='platform-detail__report-card-label'>单位成员</Text>
                  </View>
                  <View className='platform-detail__report-card'>
                    <Text className='platform-detail__report-card-num'>{report.coverage?.company_count || 0}</Text>
                    <Text className='platform-detail__report-card-label'>覆盖企业</Text>
                  </View>
                  <View className='platform-detail__report-card'>
                    <Text className='platform-detail__report-card-num'>{report.coverage?.industry_count || 0}</Text>
                    <Text className='platform-detail__report-card-label'>覆盖行业</Text>
                  </View>
                </View>

                {/* 角色分布 */}
                <View className='platform-detail__section'>
                  <Text className='platform-detail__section-title'>成员角色分布</Text>
                  <View className='platform-detail__role-distribution'>
                    <View className='platform-detail__role-row'>
                      <Text className='platform-detail__role-label'>秘书长</Text>
                      <View className='platform-detail__role-bar-track'>
                        <View
                          className='platform-detail__role-bar platform-detail__role-bar--sg'
                          style={{
                            width: `${report.total_members > 0
                              ? (report.role_distribution?.secretary_general || 0) / report.total_members * 100
                              : 0}%`
                          }}
                        />
                      </View>
                      <Text className='platform-detail__role-count'>
                        {report.role_distribution?.secretary_general || 0}
                      </Text>
                    </View>
                    <View className='platform-detail__role-row'>
                      <Text className='platform-detail__role-label'>秘书处</Text>
                      <View className='platform-detail__role-bar-track'>
                        <View
                          className='platform-detail__role-bar platform-detail__role-bar--sec'
                          style={{
                            width: `${report.total_members > 0
                              ? (report.role_distribution?.secretariat || 0) / report.total_members * 100
                              : 0}%`
                          }}
                        />
                      </View>
                      <Text className='platform-detail__role-count'>
                        {report.role_distribution?.secretariat || 0}
                      </Text>
                    </View>
                    <View className='platform-detail__role-row'>
                      <Text className='platform-detail__role-label'>成员</Text>
                      <View className='platform-detail__role-bar-track'>
                        <View
                          className='platform-detail__role-bar platform-detail__role-bar--member'
                          style={{
                            width: `${report.total_members > 0
                              ? (report.role_distribution?.member || 0) / report.total_members * 100
                              : 0}%`
                          }}
                        />
                      </View>
                      <Text className='platform-detail__role-count'>
                        {report.role_distribution?.member || 0}
                      </Text>
                    </View>
                  </View>
                </View>
              </View>
            ) : (
              <View className='platform-detail__empty'>
                <Text className='platform-detail__empty-icon'>📊</Text>
                <Text className='platform-detail__empty-title'>暂无商机数据</Text>
                <Text className='platform-detail__empty-desc'>仅秘书长可查看商业报告</Text>
              </View>
            )}
          </View>
        )}

        {/* 底部间距 */}
        <View className='platform-detail__bottom-spacer' />
      </ScrollView>

      {/* ================ 底部加入按钮 ================ */}
      <View className='platform-detail__bottom-bar'>
        <Button
          className={`platform-detail__join-btn ${alreadyJoined ? 'platform-detail__join-btn--joined' : ''}`}
          disabled={alreadyJoined || joining}
          onClick={handleJoin}
        >
          <Text className='platform-detail__join-text'>
            {alreadyJoined
              ? '已加入'
              : joining
                ? '加入中...'
                : platform.annual_fee > 0
                  ? `加入需缴纳 ¥${platform.annual_fee} /年`
                  : '免费加入'}
          </Text>
        </Button>
      </View>

      {/* ================ 邀请弹窗 ================ */}
      {showInviteModal && (
        <View className='platform-detail__modal-overlay' onClick={closeInviteModal}>
          <View className='platform-detail__modal-content' onClick={(e) => e.stopPropagation()}>
            <View className='platform-detail__modal-header'>
              <Text className='platform-detail__modal-title'>你想通过什么方式邀请?</Text>
              <Text className='platform-detail__modal-close' onClick={closeInviteModal}>
                ✕
              </Text>
            </View>
            <View className='platform-detail__modal-body'>
              <View className='platform-detail__invite-methods'>
                <View className='platform-detail__invite-method' onClick={inviteFromApp}>
                  <Text className='platform-detail__invite-icon'>📱</Text>
                  <View className='platform-detail__invite-info'>
                    <Text className='platform-detail__invite-title'>从询赋 App 中邀请</Text>
                    <Text className='platform-detail__invite-desc'>选择询赋内的好友，发送邀请链接</Text>
                  </View>
                  <Text className='platform-detail__invite-arrow'>›</Text>
                </View>
                <View className='platform-detail__invite-method' onClick={inviteFromWechat}>
                  <Text className='platform-detail__invite-icon'>💬</Text>
                  <View className='platform-detail__invite-info'>
                    <Text className='platform-detail__invite-title'>从微信邀请</Text>
                    <Text className='platform-detail__invite-desc'>选择微信好友，发送邀请链接</Text>
                  </View>
                  <Text className='platform-detail__invite-arrow'>›</Text>
                </View>
                <View className='platform-detail__invite-method' onClick={showQRCode}>
                  <Text className='platform-detail__invite-icon'>📷</Text>
                  <View className='platform-detail__invite-info'>
                    <Text className='platform-detail__invite-title'>平台二维码</Text>
                    <Text className='platform-detail__invite-desc'>通过平台二维码邀请</Text>
                  </View>
                  <Text className='platform-detail__invite-arrow'>›</Text>
                </View>
              </View>
            </View>
          </View>
        </View>
      )}
    </View>
  )
}

export default PlatformDetail
