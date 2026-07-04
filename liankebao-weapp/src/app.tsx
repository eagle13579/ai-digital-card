import { Component, ReactNode } from 'react'
import { View } from '@tarojs/components'
import ErrorBoundary from './components/ErrorBoundary'
import './app.scss'

interface AppProps {
  children?: ReactNode
}

class App extends Component<AppProps> {
  componentDidMount() {}

  componentDidShow() {}

  componentDidHide() {}

  render() {
    return (
      <ErrorBoundary>
        <View>{this.props.children}</View>
      </ErrorBoundary>
    )
  }
}

export default App
