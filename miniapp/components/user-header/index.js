/**
 * User Header — 复用用户头部组件
 * AI数智名片
 * 
 * 消除各页面重复的用户头部代码。
 * 
 * 使用方法:
 * <user-header 
 *   avatar="{{avatar}}" 
 *   name="{{name}}" 
 *   title="{{title}}"
 *   company="{{company}}"
 *   showQr="{{true}}"
 *   bind:qr="onQrTap"
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
    title: {
      type: String,
      value: '',
    },
    company: {
      type: String,
      value: '',
    },
    showQr: {
      type: Boolean,
      value: false,
    },
    showEdit: {
      type: Boolean,
      value: false,
    },
    badge: {
      type: String,
      value: '',
    },
    size: {
      type: String,
      value: 'medium', // 'small' | 'medium' | 'large'
    },
  },

  methods: {
    onQrTap() {
      this.triggerEvent('qr')
    },
    onEditTap() {
      this.triggerEvent('edit')
    },
    onAvatarTap() {
      this.triggerEvent('avatartap')
    },
  },
})
