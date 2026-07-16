/**
 * 搜索结果卡片模板组件
 *
 * 用法:
 * <result-card
 *   avatar="{{item.avatar}}"
 *   name="{{item.name}}"
 *   company="{{item.company}}"
 *   title="{{item.title}}"
 *   tags="{{item.tags}}"
 *   matchScore="{{item.matchScore}}"
 *   bind:tap="onCardTap"
 * />
 */
Component({
  properties: {
    avatar: {
      type: String,
      value: '',
    },
    name: {
      type: String,
      value: '',
    },
    company: {
      type: String,
      value: '',
    },
    title: {
      type: String,
      value: '',
    },
    tags: {
      type: Array,
      value: [],
    },
    matchScore: {
      type: Number,
      value: 0,
    },
    showMatch: {
      type: Boolean,
      value: false,
    },
    defaultAvatar: {
      type: String,
      value: '/images/default-avatar.png',
    },
    extra: {
      type: String,
      value: '',
    },
  },

  methods: {
    onTap() {
      this.triggerEvent('tap')
    },
    onAvatarError() {
      this.setData({ avatar: this.properties.defaultAvatar })
    },
  },
})
