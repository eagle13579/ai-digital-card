/**
 * 错误边界组件 - 捕获渲染错误显示友好界面
 *
 * 用法:
 * <error-boundary>
 *   <slot />  <!-- 需要容错的内容 -->
 * </error-boundary>
 *
 * 属性:
 * - fallbackTitle: 错误标题 (默认: "页面渲染异常")
 * - fallbackDesc: 错误描述 (默认: "抱歉，页面出现了一些异常")
 * - showRetry: 是否显示重试按钮 (默认: true)
 * - retryText: 重试按钮文字 (默认: "重新加载")
 */
Component({
  properties: {
    fallbackTitle: {
      type: String,
      value: '页面渲染异常',
    },
    fallbackDesc: {
      type: String,
      value: '抱歉，页面出现了一些异常',
    },
    showRetry: {
      type: Boolean,
      value: true,
    },
    retryText: {
      type: String,
      value: '重新加载',
    },
  },

  data: {
    hasError: false,
    errorInfo: '',
  },

  methods: {
    /**
     * 捕获子组件渲染错误
     */
    onCatchError(e) {
      const errMsg = (e && e.detail && e.detail.message) || '未知错误'
      console.error('[ErrorBoundary] 捕获渲染错误:', errMsg)
      this.setData({
        hasError: true,
        errorInfo: errMsg,
      })
    },

    /**
     * 重置错误状态 - 允许重新渲染
     */
    onRetry() {
      this.setData({
        hasError: false,
        errorInfo: '',
      })
      this.triggerEvent('retry')
    },

    /**
     * 手动触发错误状态（供外部调用）
     */
    triggerError(errMsg) {
      this.setData({
        hasError: true,
        errorInfo: errMsg || '未知错误',
      })
    },

    /**
     * 重置错误状态（供外部调用）
     */
    resetError() {
      this.setData({
        hasError: false,
        errorInfo: '',
      })
    },
  },
})
