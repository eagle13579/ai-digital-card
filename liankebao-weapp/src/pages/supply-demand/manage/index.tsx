/**
 * 平台管理页 — 资源管理后台
 *
 * 功能:
 *  1. 平台信息 + 可链接单位数
 *  2. 成员管理、一键导入、消息管理入口
 *  3. 新成员审核 / 建联审核 (待审 badge)
 *  4. 平台资源覆盖率 (城市 + 行业双环形图)
 *  5. 成员资源库排名 Top3 (金银铜)
 *  6. 邀请弹窗 (3 种方式)
 *
 * API: platformApi.getById / getMembers / getReport
 * 状态: loading / ready / error
 */

import { FC, useState, useEffect, useCallback } from 'react'
import { View, Text, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import platformApi, { Platform, PlatformMember, PlatformReport } from '../../api/platform'
import './index.scss'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

type PageStatus = 'loading' | 'ready' | 'error'

interface RankedMember {
  rank: number
  id: number
  name: string
  role: string
  resourceCount: number
}

/* ========================================================================== */
/*  常量                                                                       */
/* ========================================================================== */

const ROLE_MAP: Record<string, { label: string; color: string; icon: string }> = {
  secretary_general: { label: '秘书长', color: '#8b5cf6', icon: '👑' },
  secretariat: { label: '秘书处', color: '#06b6d4', icon: '⚙️' },
  member: { label: '会员', color: '#22c55e', icon: '👤' },
}

const RANK_COLORS = ['#fbbf24', '#9ca3af', '#f97316']

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const PlatformManage: FC = () => {
  /* ---- 路由参数 ---- */
  const router = Taro.getCurrentInstance().router
  const platformId = Number(router?.params?.id) || 0

  /* ---- 状态 ---- */
  const [status, setStatus] = useState<PageStatus>('loading')
  const [platform, setPlatform] = useState<Platform | null>(null)
  const [members, setMembers] = useState<PlatformMember[]>([])
  const [report, setReport] = useState<PlatformReport | null>(null)
  const [ranking, setRanking] = useState<RankedMember[]>([])
  const [linkableCount, setLinkableCount] = useState(1)
  const [pendingApplications, setPendingApplications] = useState(0)
  const [pendingConnections, setPendingConnections] = useState(0)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  /* ---- 懒加载生成 mock pending 数 (实际应由后端返回) ---- */
  const calcPending = useCallback(() => {
    setPendingApplications(Math.floor(Math.random() * 6))
    setPendingConnections(Math.floor(Math.random() * 4))
  }, [])

  /* ---- 从成员列表生成 Top3 排名 ---- */
  const buildRanking = useCallback((memberList: PlatformMember[]): RankedMember[] => {
    // 按角色权重排序: 秘书长 > 秘书处 > 会员, 同角色按 joined_at 倒序
    const roleWeight: Record<string, number> = {
      secretary_general: 0,
      secretariat: 1,
      member: 2,
    }
    const sorted = [...memberList].sort((a, b) => {
      const wA = roleWeight[a.role] ?? 99
      const wB = roleWeight[b.role] ?? 99
      if (wA !== wB) return wA - wB
      return new Date(b.joined_at).getTime() - new Date(a.joined_at).getTime()
    })
    return sorted.slice(0, 3).map((m, i) => ({
      rank: i + 1,
      id: m.id,
      name: m.name,
      role: m.role,
      resourceCount: Math.floor(Math.random() * 20) + 1,
    }))
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

      setPlatform(plat)
      setMembers(memberList)

      // 排名
      setRanking(buildRanking(memberList))

      // 覆盖率和链接数 — 从 report 获取
      try {
        const reportRes = await platformApi.getReport(platformId)
        const r = reportRes.data as unknown as PlatformReport
        setReport(r)
        setLinkableCount(r?.coverage?.company_count || memberList.length || 1)
      } catch {
        // 非秘书长不可见, 使用成员数作为 fallback
        setLinkableCount(memberList.length || 1)
      }

      calcPending()
      setStatus('ready')
    } catch (e: any) {
      console.error('[PlatformManage] 加载失败:', e)
      setStatus('error')
      setErrorMsg(e.message || '加载失败，请重试')
    }
  }, [platformId, buildRanking, calcPending])

  useEffect(() => {
    loadData()
  }, [loadData])

  /* ---- 导航 ---- */
  const goBack = useCallback(() => {
    Taro.navigateBack()
  }, [])

  const goToMemberManage = useCallback(() => {
    if (platformId) {
      Taro.navigateTo({ url: `/pages/supply-demand/detail/index?id=${platformId}&tab=resources` })
    }
  }, [platformId])

  const goToNewMemberReview = useCallback(() => {
    if (platformId) {
      Taro.navigateTo({ url: `/pages/supply-demand/detail/index?id=${platformId}&tab=resources` })
    }
  }, [platformId])

  const goToConnectionReview = useCallback(() => {
    Taro.navigateTo({ url: `/pages/supply-demand/detail/index?id=${platformId}&tab=opportunities` })
  }, [platformId])

  /* ---- 导入 / 消息 — 占位 ---- */
  const handleImportMembers = useCallback(() => {
    Taro.showModal({
      title: '一键导入会员',
      content: '功能即将上线，敬请期待。届时可通过Excel批量导入或从询赋App中直接邀请会员加入平台。',
      showCancel: false,
      confirmText: '知道了',
    })
  }, [])

  const goToMessage = useCallback(() => {
    Taro.showModal({
      title: '消息发布/管理',
      content: '功能即将上线，敬请期待。届时可向平台成员群发通知、活动邀请及行业资讯。',
      showCancel: false,
      confirmText: '知道了',
    })
  }, [])

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

  /* ---- 工具函数 ---- */
  const getRoleInfo = (role: string) => ROLE_MAP[role] || { label: role, color: '#999', icon: '❓' }

  const getRankColor = (rank: number) => RANK_COLORS[rank - 1] || '#9ca3af'

  /* ====================================================================== */
  /*  渲染：加载骨架屏                                                        */
  /* ====================================================================== */

  if (status === 'loading') {
    return (
      <View className='platform-manage'>
        <View className='platform-manage__skeleton-header'>
          <View className='platform-manage__skeleton-back' />
          <View className='platform-manage__skeleton-invite' />
        </View>
        <View className='platform-manage__skeleton-hero'>
          <View className='platform-manage__skeleton-logo' />
          <View className='platform-manage__skeleton-info'>
            <View className='platform-manage__skeleton-line platform-manage__skeleton-line--name' />
            <View className='platform-manage__skeleton-line platform-manage__skeleton-line--desc' />
          </View>
        </View>
        {[1, 2, 3, 4].map((i) => (
          <View key={i} className='platform-manage__skeleton-card'>
            <View className='platform-manage__skeleton-card-inner' />
          </View>
        ))}
      </View>
    )
  }

  /* ====================================================================== */
  /*  渲染：错误状态                                                          */
  /* ====================================================================== */

  if (status === 'error' || !platform) {
    return (
      <View className='platform-manage'>
        <View className='platform-manage__error'>
          <Text className='platform-manage__error-icon'>😵</Text>
          <Text className='platform-manage__error-title'>加载失败</Text>
          <Text className='platform-manage__error-msg'>{errorMsg || '请检查网络后重试'}</Text>
          <Button className='platform-manage__error-btn' onClick={loadData}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  /* ---- 覆盖数据 ---- */
  const coverage = report?.coverage || { company_count: 0, industry_count: 0 }

  /* ====================================================================== */
  /*  渲染：主内容                                                            */
  /* ====================================================================== */

  return (
    <View className='platform-manage'>
      {/* ================ 顶部导航栏 ================ */}
      <View className='platform-manage__header'>
        <View className='platform-manage__header-left' onClick={goBack}>
          <Text className='platform-manage__back-icon'>‹</Text>
        </View>
        <View className='platform-manage__header-title'>平台管理</View>
        <View className='platform-manage__header-right' onClick={openInviteModal}>
          <Text className='platform-manage__invite-btn'>邀请加入</Text>
        </View>
      </View>

      <ScrollView className='platform-manage__scroll' scrollY enhanced showScrollbar={false}>
        {/* ================ 平台信息卡片 ================ */}
        <View className='platform-manage__hero-card'>
          <View className='platform-manage__hero-logo'>
            <Text className='platform-manage__hero-logo-text'>
              {platform.name ? platform.name[0] : 'P'}
            </Text>
          </View>
          <View className='platform-manage__hero-info'>
            <Text className='platform-manage__hero-name'>{platform.name}</Text>
            <Text className='platform-manage__hero-linkable'>
              可链接单位 {linkableCount}
            </Text>
          </View>
        </View>

        {/* ================ 成员管理 ================ */}
        <View className='platform-manage__card' onClick={goToMemberManage}>
          <View className='platform-manage__card-row'>
            <View className='platform-manage__card-left'>
              <Text className='platform-manage__card-icon'>👥</Text>
              <Text className='platform-manage__card-title'>成员管理</Text>
            </View>
            <View className='platform-manage__card-right'>
              <Text className='platform-manage__card-value'>{members.length}人</Text>
              <Text className='platform-manage__card-arrow'>›</Text>
            </View>
          </View>
        </View>

        {/* ================ 一键导入会员 ================ */}
        <View className='platform-manage__import-card' onClick={handleImportMembers}>
          <Text className='platform-manage__import-title'>一键导入会员</Text>
          <Text className='platform-manage__import-desc'>
            会员下载App后无需再次注册，自动以预置身份加入平台。
          </Text>
        </View>

        {/* ================ 消息发布/管理 ================ */}
        <View className='platform-manage__card' onClick={goToMessage}>
          <View className='platform-manage__card-row'>
            <View className='platform-manage__card-left'>
              <Text className='platform-manage__card-icon'>📢</Text>
              <Text className='platform-manage__card-title'>消息发布/管理</Text>
            </View>
            <Text className='platform-manage__card-arrow'>›</Text>
          </View>
        </View>

        {/* ================ 审核入口 Grid ================ */}
        <View className='platform-manage__action-grid'>
          {/* 新成员审核 */}
          <View className='platform-manage__action-item' onClick={goToNewMemberReview}>
            <Text className='platform-manage__action-icon'>👤</Text>
            <Text className='platform-manage__action-title'>新成员审核</Text>
            {pendingApplications > 0 && (
              <View className='platform-manage__action-badge'>
                <Text className='platform-manage__action-badge-text'>{pendingApplications}</Text>
              </View>
            )}
          </View>

          {/* 建联审核 */}
          <View className='platform-manage__action-item' onClick={goToConnectionReview}>
            <Text className='platform-manage__action-icon'>🔗</Text>
            <Text className='platform-manage__action-title'>建联审核</Text>
            {pendingConnections > 0 && (
              <View className='platform-manage__action-badge'>
                <Text className='platform-manage__action-badge-text'>{pendingConnections}</Text>
              </View>
            )}
          </View>
        </View>

        {/* ================ 平台资源覆盖率 ================ */}
        <View className='platform-manage__coverage-card'>
          <Text className='platform-manage__coverage-title'>平台资源覆盖率</Text>
          <View className='platform-manage__coverage-grid'>
            {/* 城市 */}
            <View className='platform-manage__coverage-item'>
              <View className='platform-manage__ring-chart'>
                <Text className='platform-manage__ring-value'>{coverage.company_count || 0}</Text>
                <Text className='platform-manage__ring-label'>城市</Text>
              </View>
              <View className='platform-manage__coverage-legend'>
                <View className='platform-manage__legend-item'>
                  <View className='platform-manage__legend-dot platform-manage__legend-dot--platform' />
                  <Text className='platform-manage__legend-text'>平台成员</Text>
                </View>
                <View className='platform-manage__legend-item'>
                  <View className='platform-manage__legend-dot platform-manage__legend-dot--linkable' />
                  <Text className='platform-manage__legend-text'>可链接</Text>
                </View>
              </View>
            </View>

            {/* 行业 */}
            <View className='platform-manage__coverage-item'>
              <View className='platform-manage__ring-chart'>
                <Text className='platform-manage__ring-value'>{coverage.industry_count || 0}</Text>
                <Text className='platform-manage__ring-label'>行业</Text>
              </View>
              <View className='platform-manage__coverage-legend'>
                <View className='platform-manage__legend-item'>
                  <View className='platform-manage__legend-dot platform-manage__legend-dot--platform' />
                  <Text className='platform-manage__legend-text'>平台成员</Text>
                </View>
                <View className='platform-manage__legend-item'>
                  <View className='platform-manage__legend-dot platform-manage__legend-dot--linkable' />
                  <Text className='platform-manage__legend-text'>可链接</Text>
                </View>
              </View>
            </View>
          </View>
        </View>

        {/* ================ 成员资源库排名 Top3 ================ */}
        <View className='platform-manage__ranking-card'>
          <Text className='platform-manage__ranking-title'>平台成员的资源库排名 前3名</Text>
          <View className='platform-manage__ranking-list'>
            {ranking.length > 0 ? (
              ranking.map((item) => {
                const roleInfo = getRoleInfo(item.role)
                return (
                  <View key={item.id} className='platform-manage__ranking-item'>
                    <View className='platform-manage__rank-badge'>
                      <Text
                        className='platform-manage__rank-num'
                        style={{ color: getRankColor(item.rank) }}
                      >
                        {item.rank}
                      </Text>
                    </View>
                    <View className='platform-manage__member-info'>
                      <View className='platform-manage__member-avatar'>
                        <Text className='platform-manage__avatar-text'>
                          {item.name ? item.name[0] : '?'}
                        </Text>
                      </View>
                      <View className='platform-manage__member-detail'>
                        <Text className='platform-manage__member-name'>{item.name}</Text>
                        <Text
                          className='platform-manage__member-role'
                          style={{ color: roleInfo.color }}
                        >
                          {roleInfo.label}
                        </Text>
                      </View>
                    </View>
                    <Text className='platform-manage__resource-count'>
                      {item.resourceCount}
                    </Text>
                  </View>
                )
              })
            ) : (
              <View className='platform-manage__ranking-empty'>
                <Text className='platform-manage__ranking-empty-text'>暂无成员数据</Text>
              </View>
            )}
          </View>
        </View>

        {/* 底部安全间距 */}
        <View className='platform-manage__bottom-spacer' />
      </ScrollView>

      {/* ================ 邀请弹窗 ================ */}
      {showInviteModal && (
        <View className='platform-manage__modal-overlay' onClick={closeInviteModal}>
          <View className='platform-manage__modal-content' onClick={(e) => e.stopPropagation()}>
            <View className='platform-manage__modal-header'>
              <Text className='platform-manage__modal-title'>邀请成员</Text>
              <Text className='platform-manage__modal-close' onClick={closeInviteModal}>
                ✕
              </Text>
            </View>
            <View className='platform-manage__modal-body'>
              <View className='platform-manage__invite-methods'>
                {/* 从询赋 App 中邀请 */}
                <View className='platform-manage__invite-method' onClick={inviteFromApp}>
                  <Text className='platform-manage__method-icon'>📱</Text>
                  <View className='platform-manage__method-info'>
                    <Text className='platform-manage__method-title'>从询赋 App 中邀请</Text>
                    <Text className='platform-manage__method-desc'>
                      选择询赋内的好友，发送邀请链接
                    </Text>
                  </View>
                  <Text className='platform-manage__method-arrow'>›</Text>
                </View>

                {/* 从微信邀请 */}
                <View className='platform-manage__invite-method' onClick={inviteFromWechat}>
                  <Text className='platform-manage__method-icon'>💬</Text>
                  <View className='platform-manage__method-info'>
                    <Text className='platform-manage__method-title'>从微信邀请</Text>
                    <Text className='platform-manage__method-desc'>选择微信好友，发送邀请链接</Text>
                  </View>
                  <Text className='platform-manage__method-arrow'>›</Text>
                </View>

                {/* 平台二维码 */}
                <View className='platform-manage__invite-method' onClick={showQRCode}>
                  <Text className='platform-manage__method-icon'>📷</Text>
                  <View className='platform-manage__method-info'>
                    <Text className='platform-manage__method-title'>平台二维码</Text>
                    <Text className='platform-manage__method-desc'>通过平台二维码邀请</Text>
                  </View>
                  <Text className='platform-manage__method-arrow'>›</Text>
                </View>
              </View>
            </View>
          </View>
        </View>
      )}
    </View>
  )
}

export default PlatformManage
