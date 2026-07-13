/**
 * Stats Grid — 复用统计网格组件
 * AI数智名片
 * 
 * 消除各处重复的统计卡片网格，统一数据展示样式。
 * 
 * 使用方法:
 * <stats-grid items="{{stats}}" />
 * 
 * items: [{ icon, label, value, color, trend }]
 */
Component({
  properties: {
    items: {
      type: Array,
      value: [],
    },
    columns: {
      type: Number,
      value: 3,
    },
    size: {
      type: String,
      value: 'medium', // 'small' | 'medium' | 'large'
    },
  },

  data: {
    gridClass: '',
  },

  observers: {
    columns(cols) {
      this.setData({
        gridClass: `cols-${Math.min(Math.max(cols, 2), 4)}`,
      })
    },
    size(sz) {
      this.setData({
        sizeClass: `size-${sz}`,
      })
    },
  },

  lifetimes: {
    attached() {
      this.setData({
        gridClass: `cols-${Math.min(Math.max(this.properties.columns, 2), 4)}`,
        sizeClass: `size-${this.properties.size}`,
      })
    },
  },
})
