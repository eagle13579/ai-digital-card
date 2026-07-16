/**
 * 标签列表组件 - 可点击筛选
 *
 * 用法:
 * <tag-list tags="{{tags}}" selected="{{selectedTags}}" bind:tap="onTagTap" />
 */
Component({
  properties: {
    tags: {
      type: Array,
      value: [],
    },
    selected: {
      type: Array,
      value: [],
    },
    type: {
      type: String,
      value: '',  // provide | need | ''
    },
    selectable: {
      type: Boolean,
      value: true,
    },
    maxItems: {
      type: Number,
      value: 0,  // 0 = 不限制
    },
  },

  methods: {
    onTap(e) {
      const index = e.currentTarget.dataset.index
      const tag = this.properties.tags[index]
      if (this.properties.selectable) {
        this.triggerEvent('tap', { index, tag })
      }
    },
  },
})
