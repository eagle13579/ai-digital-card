import { FC, useState, useRef, useEffect } from 'react'
import { View, Text, Input, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { chatApi } from '../../api/digitalBrochure'
import './index.scss'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const AiChat: FC = () => {
  const [msgs, setMsgs] = useState<Message[]>([
    { role: 'assistant', content: '你好！我是AI助手，可以帮你分析名片、推荐人脉、优化画册。有什么需要？' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<any>(null)

  useEffect(() => { scrollToBottom() }, [msgs])
  const scrollToBottom = () => {
    setTimeout(() => scrollRef.current?.scrollTo(0, 9999), 100)
  }

  const send = async () => {
    if (!input.trim() || loading) return
    const text = input.trim()
    setInput('')
    setMsgs(p => [...p, { role: 'user', content: text }])
    setLoading(true)
    try {
      const res = await chatApi.sendMessage({
        messages: [...msgs, { role: 'user', content: text }].map(m => ({
          role: m.role, content: m.content
        }))
      })
      setMsgs(p => [...p, { role: 'assistant', content: res.reply }])
    } catch {
      setMsgs(p => [...p, { role: 'assistant', content: '抱歉，AI服务暂时不可用' }])
    } finally { setLoading(false) }
  }

  return (
    <View className='ai-chat'>
      <ScrollView className='ai-chat__msgs' scrollY ref={scrollRef}>
        {msgs.map((m, i) => (
          <View key={i} className={`ai-chat__msg ai-chat__msg--${m.role}`}>
            <Text className='ai-chat__txt'>{m.content}</Text>
          </View>
        ))}
        {loading && <View className='ai-chat__typing'><Text>AI思考中...</Text></View>}
      </ScrollView>
      <View className='ai-chat__bar'>
        <Input
          className='ai-chat__inp'
          value={input}
          onInput={(e) => setInput(e.detail.value)}
          placeholder='输入消息...'
          confirmType='send'
          onConfirm={send}
        />
        <Button className='ai-chat__btn' onClick={send} disabled={loading}>发送</Button>
      </View>
    </View>
  )
}
export default AiChat
