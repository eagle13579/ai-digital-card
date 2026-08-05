/**
 * 骨架屏组件
 * 支持多种骨架类型: card, list, profile, details, stats
 *
 * 用法:
 * <skeleton type="card" loading="{{true}}" />
 * <skeleton type="list" loading="{{true}}" count="5" />
 */
Component({
  properties: {
    loading: {
      type: Boolean,
      value: true,
    },
    type: {
      type: String,
      value: 'card',  // card | list | profile | details | stats
    },
    count: {
      type: Number,
      value: 1,  // list类型时重复条数
    },
  },
})
