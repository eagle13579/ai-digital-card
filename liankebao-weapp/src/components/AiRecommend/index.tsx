import { FC, useState, useEffect } from 'react'
import { View, Text, Image, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import matchApi from '../../api/match'
import './index.scss'

interface RecommendItem {
  card_id: string
  name: string
  company: string
  title: string
  avatar: string
  match_score: number
  match_reason: string
}

const AiRecommend: FC = () => {
  const [items, setItems] = useState<RecommendItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      const res = await matchApi.getHybridRecommend('hot')
      setItems(res?.list || [])
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }

  const goCard = (id: string) => {
    Taro.navigateTo({ url: `/pages/network/index?id=${id}` })
  }

  if (loading) return (
    <View className='ai-rec'>
      <View className='ai-rec__hdr'>
        <Text className='ai-rec__ttl'>AI 推荐</Text>
      </View>
      <View className='ai-rec__ldr'><Text>加载中...</Text></View>
    </View>
  )
  if (!items.length) return null

  return (
    <View className='ai-rec'>
      <View className='ai-rec__hdr'>
        <Text className='ai-rec__ttl'>AI 推荐</Text>
        <Text className='ai-rec__sub'>基于AI分析</Text>
      </View>
      <ScrollView scrollX className='ai-rec__list'>
        {items.slice(0, 6).map((it) => (
          <View key={it.card_id} className='ai-rec__card' onClick={() => goCard(it.card_id)}>
            <Image className='ai-rec__avt' src={it.avatar} />
            <Text className='ai-rec__nm'>{it.name}</Text>
            <Text className='ai-rec__co'>{it.company}</Text>
            <View className='ai-rec__sc'><Text>{it.match_score}%</Text></View>
            {it.match_reason && <Text className='ai-rec__rs'>{it.match_reason}</Text>}
          </View>
        ))}
      </ScrollView>
    </View>
  )
}
export default AiRecommend
