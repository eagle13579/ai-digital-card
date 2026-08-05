/**
 * 页面标题栏组件 - 统一页面标题栏风格
 *
 * 用法:
 * <!-- 基本用法 -->
 * <page-header title="增长看板" />
 *
 * <!-- 带副标题 -->
 * <page-header title="增长看板" subtitle="注册 → 名片 → 匹配 → 连接" />
 *
 * 属性:
 * - title: 主标题 (必填)
 * - subtitle: 副标题 (可选)
 * - titleColor: 标题颜色 (默认: 继承)
 * - subtitleColor: 副标题颜色 (默认: 继承)
 * - icon: 标题前的图标 (可选, 如: "📊")
 * - size: 尺寸, "lg" 大 / "md" 中 (默认: "lg")
 *
 * 事件:
 * - back: 点击返回按钮 (默认 wx.navigateBack)
 */
Component({
  properties: {
    title: {
      type: String,
      value: '',
    },
    subtitle: {
      type: String,
      value: '',
    },
    titleColor: {
      type: String,
      value: '',
    },
    subtitleColor: {
      type: String,
      value: '',
    },
    icon: {
      type: String,
      value: '',
    },
    size: {
      type: String,
      value: 'lg', // 'lg' | 'md'
    },
    showBack: {
      type: Boolean,
      value: false,
    },
  },

  data: {
    titleStyle: '',
    subtitleStyle: '',
  },

  observers: {
    titleColor(v) {
      this.setData({
        titleStyle: v ? `color: ${v};` : '',
      })
    },
    subtitleColor(v) {
      this.setData({
        subtitleStyle: v ? `color: ${v};` : '',
      })
    },
  },

  methods: {
    onBack() {
      this.triggerEvent('back')
      wx.navigateBack({ delta: 1 })
    },
  },
})
