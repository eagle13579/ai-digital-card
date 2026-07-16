/**
 * 统计数字网格组件
 *
 * 用法:
 * <stats-grid items="{{stats}}" />
 * stats = [{ label: '访客', value: 128, key: 'visitors', icon: '👁' }, ...]
 */
Component({
  properties: {
    items: {
      type: Array,
      value: [],
    },
    columns: {
      type: Number,
      value: 4,  // 2 | 3 | 4
    },
  },
})
