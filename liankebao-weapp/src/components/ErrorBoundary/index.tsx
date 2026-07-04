import { Component, ErrorInfo, ReactNode } from 'react'
import { View, Button, Text } from '@tarojs/components'
import './index.scss'

interface Props {
  children?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <View className='error-boundary'>
          <View className='error-boundary__content'>
            <Text className='error-boundary__icon'>⚠️</Text>
            <Text className='error-boundary__title'>出错了</Text>
            <Text className='error-boundary__message'>
              {this.state.error?.message || '页面渲染异常'}
            </Text>
            <Button className='error-boundary__btn' onClick={this.handleRetry}>
              点击重试
            </Button>
          </View>
        </View>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
