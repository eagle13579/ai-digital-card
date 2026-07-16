/**
 * 用户头像组件
 * 支持在线/离线/会员边框
 *
 * 用法:
 * <user-avatar src="{{url}}" size="large" status="online" memberLevel="gold" />
 */
Component({
  properties: {
    src: {
      type: String,
      value: '',
    },
    size: {
      type: String,
      value: 'medium', // small | medium | large
    },
    status: {
      type: String,
      value: '',      // online | offline | busy | ''
    },
    memberLevel: {
      type: String,
      value: '',      // free | gold | diamond | board
    },
    defaultAvatar: {
      type: String,
      value: '/images/default-avatar.png',
    },
  },

  data: {
    imageUrl: '',
  },

  observers: {
    'src': function (val) {
      this.setData({ imageUrl: val || this.properties.defaultAvatar })
    },
  },

  methods: {
    onError() {
      this.setData({ imageUrl: this.properties.defaultAvatar })
    },
    onTap() {
      this.triggerEvent('tap')
    },
  },
})
