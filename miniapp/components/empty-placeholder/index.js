/**
 * 空状态占位组件 — 插画 + 引导文字 + CTA按钮
 *
 * 用法:
 * <empty-placeholder
 *   icon="📭"
 *   title="{{_t.noData}}"
 *   desc="快去创建你的名片吧"
 *   ctaText="{{_t.createCard}}"
 *   showCta="{{true}}"
 *   bind:cta="onCreateCard"
 * />
 */
const i18n = require('../../utils/i18n')

Component({
  properties: {
    icon: {
      type: String,
      value: '📭',
    },
    title: {
      type: String,
      value: '',
    },
    desc: {
      type: String,
      value: '',
    },
    ctaText: {
      type: String,
      value: '',
    },
    showCta: {
      type: Boolean,
      value: true,
    },
  },

  data: {
    _t: {},
  },

  lifetimes: {
    attached() {
      this.setData({ _t: i18n.getTranslations() })
    },
  },

  methods: {
    onCta() {
      this.triggerEvent('cta')
    },
  },
})
