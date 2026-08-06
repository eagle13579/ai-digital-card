import { FC, useState, useEffect, useCallback } from 'react'
import { View, Text, Image, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { api } from '../../api/client'
import './index.scss'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

interface VisitorItem {
  visitor_name: string
  visitor_avatar: string
  visit_time: string
  source: string
  brochure_id: string
}

type PageStatus = 'loading' | 'ready' | 'error'

/* ========================================================================== */
/*  相对时间工具                                                               */
/* ========================================================================== */

function formatRelativeTime(timeStr: string): string {
  const now = Date.now()
  const time = new Date(timeStr).getTime()
  const diff = Math.floor((now - time) / 1000)

  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return `${Math.floor(diff / 86400)}天前`
}

/* ========================================================================== */
/*  来源标签配置                                                               */
/* ========================================================================== */

const SOURCE_LABEL_MAP: Record<string, string> = {
  share: '分享',
  scan: '扫码',
  recommend: '推荐',
}

function getSourceLabel(source: string): string {
  return SOURCE_LABEL_MAP[source] || source
}

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Visitors: FC = () => {
  const [status, setStatus] = useState<PageStatus>('loading')
  const [visitors, setVisitors] = useState<VisitorItem[]>([])
  const [errorMsg, setErrorMsg] = useState('')

  /* ---- 加载访客记录 ---- */
  const loadVisitors = useCallback(async () => {
    setStatus('loading')
    setErrorMsg('')
    try {
      const brochureId = Taro.getStorageSync('cardId')
      if (!brochureId) {
        setVisitors([])
        setStatus('ready')
        return
      }
      const res = await api.get<VisitorItem[]>(`/api/v1/visitors/${brochureId}`)
      if (res.code === 200 || res.code === 0) {
        setVisitors(res.data || [])
        setStatus('ready')
      } else {
        setErrorMsg(res.message || '加载失败')
        setStatus('error')
      }
    } catch (e: any) {
      setErrorMsg(e.message || '网络错误，请检查网络连接')
      setStatus('error')
    }
  }, [])

  useEffect(() => {
    loadVisitors()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* ---- 邀请分享 ---- */
  const handleInviteShare = useCallback(() => {
    Taro.setClipboardData({
      data: 'https://liankebao.app/card',
      success: () => {
        Taro.showToast({ title: '名片链接已复制', icon: 'success' })
      },
      fail: () => {
        Taro.showToast({ title: '复制失败', icon: 'none' })
      },
    })
  }, [])

  /* ================================================================ */
  /*  渲染：各状态                                                      */
  /* ================================================================ */

  /* ---- loading: 骨架屏 ---- */
  if (status === 'loading') {
    return (
      <View className='visitors'>
        <View className='visitors__skeleton'>
          <View className='visitors__skeleton-header'>
            <View className='visitors__skeleton-title' />
            <View className='visitors__skeleton-count' />
          </View>
          {[1, 2, 3, 4, 5].map((i) => (
            <View key={i} className='visitors__skeleton-item'>
              <View className='visitors__skeleton-avatar' />
              <View className='visitors__skeleton-info'>
                <View className='visitors__skeleton-name' />
                <View className='visitors__skeleton-time' />
              </View>
              <View className='visitors__skeleton-tag' />
            </View>
          ))}
        </View>
      </View>
    )
  }

  /* ---- error: 错误状态 ---- */
  if (status === 'error') {
    return (
      <View className='visitors'>
        <View className='visitors__error'>
          <Text className='visitors__error-icon'>😵</Text>
          <Text className='visitors__error-title'>加载失败</Text>
          <Text className='visitors__error-message'>{errorMsg || '请检查网络后重试'}</Text>
          <Button className='visitors__error-btn' onClick={loadVisitors}>
            重新加载
          </Button>
        </View>
      </View>
    )
  }

  /* ---- ready: 空态 ---- */
  if (visitors.length === 0) {
    return (
      <View className='visitors'>
        <View className='visitors__empty'>
          <Text className='visitors__empty-icon'>👀</Text>
          <Text className='visitors__empty-title'>还没有人看过您的名片</Text>
          <Text className='visitors__empty-desc'>分享名片给好友，让更多人认识您</Text>
          <Button className='visitors__empty-btn' onClick={handleInviteShare}>
            邀请好友查看
          </Button>
        </View>
      </View>
    )
  }

  /* ---- ready: 列表 ---- */
  return (
    <View className='visitors'>
      <View className='visitors__header'>
        <Text className='visitors__header-title'>访客记录</Text>
        <Text className='visitors__header-count'>共 {visitors.length} 位访客</Text>
      </View>

      <ScrollView className='visitors__scroll' scrollY enhanced showScrollbar={false}>
        <View className='visitors__list'>
          {visitors.map((visitor, index) => (
            <View key={`${visitor.brochure_id}-${index}`} className='visitors__card'>
              <Image
                className='visitors__avatar'
                src={visitor.visitor_avatar || 'https://via.placeholder.com/80'}
                mode='aspectFill'
              />
              <View className='visitors__info'>
                <Text className='visitors__name'>{visitor.visitor_name || '匿名访客'}</Text>
                <Text className='visitors__time'>{formatRelativeTime(visitor.visit_time)}</Text>
              </View>
              <View className='visitors__source-tag'>
                <Text className='visitors__source-text'>{getSourceLabel(visitor.source)}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* 底部间距 */}
        <View className='visitors__bottom-spacer' />
      </ScrollView>
    </View>
  )
}

export default Visitors
