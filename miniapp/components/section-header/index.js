/**
 * 标题栏组件 - 带"查看更多"链接
 *
 * 用法:
 * <section-header title="{{_t.myCard}}" more="{{_t.viewAll}}" bind:more="onViewMore" />
 */
Component({
  properties: {
    title: {
      type: String,
      value: '',
    },
    more: {
      type: String,
      value: '',
    },
    showMore: {
      type: Boolean,
      value: true,
    },
  },

  methods: {
    onMore() {
      this.triggerEvent('more')
    },
  },
})
