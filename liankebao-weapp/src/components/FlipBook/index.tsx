import { PLACEHOLDER } from '../../constants/placeholder'
import { FC, useState } from 'react'
import { View, Image, Text } from '@tarojs/components'
import './index.scss'

interface FlipBookProps {
  cardData?: {
    id?: string
    name?: string
    company?: string
    title?: string
    phone?: string
    email?: string
    avatar?: string
    bg_image?: string
    wechat_qrcode?: string
  }
  /** 是否可翻转 */
  flippable?: boolean
  /** 默认显示面: 'front' | 'back' */
  defaultSide?: 'front' | 'back'
  /** 是否在加载中 */
  loading?: boolean
  /** 自定义样式 */
  className?: string
  /** 翻转回调 */
  onFlip?: (side: 'front' | 'back') => void
}

const FlipBook: FC<FlipBookProps> = ({
  cardData,
  flippable = true,
  defaultSide = 'front',
  loading = false,
  className = '',
  onFlip,
}) => {
  const [flipped, setFlipped] = useState(defaultSide === 'back')

  const handleFlip = () => {
    if (!flippable || loading) return
    const newFlipped = !flipped
    setFlipped(newFlipped)
    onFlip?.(newFlipped ? 'back' : 'front')
  }

  // 加载骨架
  if (loading) {
    return (
      <View className={`flipbook ${className}`}>
        <View className='flipbook__inner flipbook__inner--loading'>
          <View className='flipbook__skeleton'>
            <View className='flipbook__skeleton-avatar' />
            <View className='flipbook__skeleton-line flipbook__skeleton-line--short' />
            <View className='flipbook__skeleton-line flipbook__skeleton-line--medium' />
            <View className='flipbook__skeleton-line flipbook__skeleton-line--long' />
          </View>
        </View>
      </View>
    )
  }

  // 空名片占位
  if (!cardData) {
    return (
      <View className={`flipbook ${className}`} onClick={handleFlip}>
        <View className='flipbook__inner'>
          <View className='flipbook__empty'>
            <Text className='flipbook__empty-icon'>📇</Text>
            <Text className='flipbook__empty-text'>暂无名片</Text>
            <Text className='flipbook__empty-hint'>点击创建您的数字名片</Text>
          </View>
        </View>
      </View>
    )
  }

  return (
    <View
      className={`flipbook ${className} ${flipped ? 'flipbook--flipped' : ''}`}
      onClick={handleFlip}
    >
      <View className='flipbook__inner'>
        {/* 正面 */}
        <View
          className='flipbook__face flipbook__face--front'
          style={{
            background: cardData.bg_image
              ? `url(${cardData.bg_image}) center/cover no-repeat`
              : 'linear-gradient(135deg, #1677ff 0%, #0958d9 100%)',
          }}
        >
          <View className='flipbook__front-content'>
            <Image
              className='flipbook__avatar'
              src={cardData.avatar || PLACEHOLDER.avatar120}
              mode='aspectFill'
            />
            <Text className='flipbook__name'>{cardData.name || '未设置姓名'}</Text>
            <Text className='flipbook__company'>
              {[cardData.company, cardData.title].filter(Boolean).join(' · ') || '未设置公司信息'}
            </Text>
            <View className='flipbook__divider' />
            <View className='flipbook__contact'>
              {cardData.phone && <Text className='flipbook__contact-item'>📞 {cardData.phone}</Text>}
              {cardData.email && <Text className='flipbook__contact-item'>📧 {cardData.email}</Text>}
            </View>
          </View>
          {flippable && <Text className='flipbook__hint'>点击翻转</Text>}
        </View>

        {/* 背面 */}
        <View className='flipbook__face flipbook__face--back'>
          <View className='flipbook__back-content'>
            <Text className='flipbook__back-title'>微信联系我</Text>
            {cardData.wechat_qrcode ? (
              <Image
                className='flipbook__qrcode'
                src={cardData.wechat_qrcode}
                mode='aspectFit'
              />
            ) : (
              <View className='flipbook__qrcode-placeholder'>
                <Text className='flipbook__qrcode-placeholder-icon'>📱</Text>
                <Text className='flipbook__qrcode-placeholder-text'>暂未设置微信二维码</Text>
              </View>
            )}
            <Text className='flipbook__back-hint'>扫码添加微信</Text>
          </View>
          {flippable && <Text className='flipbook__hint'>点击翻转</Text>}
        </View>
      </View>
    </View>
  )
}

export default FlipBook
