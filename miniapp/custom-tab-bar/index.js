// 自定义TabBar组件 - 暗色极简+紫色主题 (i18n enabled)
const i18n = require('../utils/i18n')

Component({
  properties: {
    selected: {
      type: Number,
      value: 0
    }
  },

  data: {
    color: "rgba(255,255,255,0.4)",
    selectedColor: "#a78bfa",
    list: []
  },

  lifetimes: {
    attached() {
      this._updateTabs()
    }
  },

  pageLifetimes: {
    show() {
      this._updateTabs()
    }
  },

  methods: {
    _updateTabs() {
      const tabs = [
        {
          pagePath: "pages/index/index",
          text: i18n.t('tabHome'),
          iconPath: "/images/tab-home.png",
          selectedIconPath: "/images/tab-home-active.png",
          icon: "🏠"
        },
        {
          pagePath: "pages/card/card",
          text: i18n.t('tabCard'),
          iconPath: "/images/tab-card.png",
          selectedIconPath: "/images/tab-card-active.png",
          icon: "📇"
        },
        {
          pagePath: "pages/profile/profile",
          text: i18n.t('tabProfile'),
          iconPath: "/images/tab-profile.png",
          selectedIconPath: "/images/tab-profile-active.png",
          icon: "👤"
        }
      ]
      this.setData({ list: tabs })
    },

    switchTab(e) {
      const data = e.currentTarget.dataset
      const url = '/' + data.path
      wx.switchTab({ url })
    }
  }
})
