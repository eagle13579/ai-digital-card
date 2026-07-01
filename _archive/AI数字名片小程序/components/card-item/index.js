/**
 * 名片卡片组件
 * 属性：
 * - card: 名片数据对象
 * - showMatch: 是否显示匹配度
 * - showUnlock: 是否显示解锁按钮
 */
Component({
  properties: {
    card: {
      type: Object,
      value: {},
    },
    showMatch: {
      type: Boolean,
      value: false,
    },
    showUnlock: {
      type: Boolean,
      value: false,
    },
  },

  data: {
    memberLevelText: '',
  },

  observers: {
    'card.memberLevel': function (level) {
      const map = { free: 'Free', gold: 'Gold', diamond: 'Diamond', board: 'Board' }
      this.setData({ memberLevelText: map[level] || 'Free' })
    },
  },

  methods: {
    onTap() {
      this.triggerEvent('tap', { card: this.properties.card })
    },
    onUnlock(e) {
      this.triggerEvent('unlock', { card: this.properties.card })
    },
  },
})
