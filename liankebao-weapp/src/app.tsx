import { Component, ReactNode } from 'react'
import { View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import ErrorBoundary from './components/ErrorBoundary'
import './app.scss'

interface AppProps {
  children?: ReactNode
}

class App extends Component<AppProps> {
  componentDidMount() {
    // 初始化分享裂变系统：检查并清理过期分享记录
    this.cleanupExpiredShareRecords()
  }

  componentDidShow() {}

  componentDidHide() {}

  /**
   * 清理过期分享次数记录（只保留最近 7 天）
   * 每天的记录格式：share_count_YYYYMMDD
   */
  private cleanupExpiredShareRecords() {
    try {
      const now = new Date()
      const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      const cutoffKey = `share_count_${sevenDaysAgo.getFullYear()}${String(sevenDaysAgo.getMonth() + 1).padStart(2, '0')}${String(sevenDaysAgo.getDate()).padStart(2, '0')}`

      // 遍历 storage 删除过期分享记录
      const allKeys = Taro.getStorageInfoSync().keys
      for (const key of allKeys) {
        if (key.startsWith('share_count_') && key < cutoffKey) {
          Taro.removeStorageSync(key)
        }
      }
    } catch {
      // 清理失败不影响主流程
    }
  }

  render() {
    return (
      <ErrorBoundary>
        <View>{this.props.children}</View>
      </ErrorBoundary>
    )
  }
}

export default App
