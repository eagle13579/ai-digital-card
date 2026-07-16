/**
 * 冷启动引导流组件
 * 用户首次登录后自动弹出，3步引导
 */
const store = require('../../utils/store')
const i18n = require('../../utils/i18n')

Component({
  properties: {
    visible: {
      type: Boolean,
      value: false,
    },
    steps: {
      type: Array,
      value: [
        { icon: '✎', title: i18n.t('guideStep1Title'), desc: i18n.t('guideStep1Desc') },
        { icon: '◇', title: i18n.t('guideStep2Title'), desc: i18n.t('guideStep2Desc') },
        { icon: '↗', title: i18n.t('guideStep3Title'), desc: i18n.t('guideStep3Desc') },
      ],
    },
  },

  data: {
    currentStep: 1,
    _t: {},
  },

  lifetimes: {
    attached() {
      this.setData({ _t: i18n.getTranslations() })
    },
  },

  observers: {
    'visible': function (val) {
      if (val) {
        this.setData({ currentStep: 1 })
      }
    },
  },

  methods: {
    /** 下一步 */
    nextStep() {
      const next = this.data.currentStep + 1
      if (next > 3) {
        this.close()
      } else {
        this.setData({ currentStep: next })
      }
    },

    /** 上一步 */
    prevStep() {
      if (this.data.currentStep > 1) {
        this.setData({ currentStep: this.data.currentStep - 1 })
      }
    },

    /** 关闭并标记引导完成 */
    close() {
      this.setData({ currentStep: 1 })
      store.setOnboardingDone()
      this.triggerEvent('close')
    },

    /** 跳过引导 */
    skip() {
      this.setData({ currentStep: 1 })
      store.setOnboardingDone()
      wx.showToast({ title: i18n.t('guideSkipped'), icon: 'none' })
      this.triggerEvent('skip')
    },

    /** 阻止遮罩点击穿透 */
    noop() {
      // do nothing
    },
  },
})
