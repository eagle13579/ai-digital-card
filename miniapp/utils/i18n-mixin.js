/**
 * i18n Mixin — 全局 i18n 注入工具
 * AI数智名片
 * 
 * 封装 i18n 注入方法，消除 Page/Component 中重复的 _t 注入代码。
 * 使用方式:
 *   const i18nMixin = require('../../utils/i18n-mixin')
 *   Page(i18nMixin.attach({
 *     data: { ... },
 *     onLoad() { ... },
 *   }))
 * 
 * 自动在 onLoad/attached 时注入 this.data._t
 * 提供 this.t(key, params) 快捷方法获取翻译文本
 * 提供 this.tArray(key) 快捷方法获取数组翻译
 */
const i18n = require('./i18n')

/**
 * 注入 i18n 工具到页面/组件
 * @param {object} pageOptions - Page() 或 Component() 的配置对象
 * @param {object} [options] - 额外选项
 * @param {string} [options.lifecycle] - 生命周期钩子名，Page 用 'onLoad'，Component 用 'attached'
 * @returns {object} 增强后的配置对象
 */
function attach(pageOptions, options = {}) {
  const lifecycle = options.lifecycle || 'onLoad'
  const origLifecycle = pageOptions[lifecycle]

  // 注入 _t 数据到 data
  pageOptions[lifecycle] = function (...args) {
    // 注入翻译对象
    this.setData({ _t: i18n.getTranslations() })
    // 调用原始生命周期
    if (origLifecycle) {
      return origLifecycle.apply(this, args)
    }
  }

  // 提供 this.t() 快捷方法
  pageOptions.t = function (key, params) {
    return i18n.t(key, params)
  }

  // 提供 this.tArray() 快捷方法
  pageOptions.tArray = function (key) {
    return i18n.tArray(key)
  }

  // 如果存在 onShow，重新注入翻译（语言可能已切换）
  const origOnShow = pageOptions.onShow
  if (origOnShow) {
    const originalOnShow = origOnShow
    pageOptions.onShow = function (...args) {
      // 每次显示时刷新翻译（支持动态切换语言）
      if (this.data._t) {
        this.setData({ _t: i18n.getTranslations() })
      } else {
        this.setData({ _t: i18n.getTranslations() })
      }
      return originalOnShow.apply(this, args)
    }
  } else {
    pageOptions.onShow = function () {
      this.setData({ _t: i18n.getTranslations() })
    }
  }

  return pageOptions
}

/**
 * 刷新页面翻译数据（语言切换后调用）
 * @param {object} page - 页面实例（通常传 this）
 */
function refresh(page) {
  if (page && page.setData) {
    page.setData({ _t: i18n.getTranslations() })
  }
}

/**
 * 获取当前翻译对象
 */
function getTranslations() {
  return i18n.getTranslations()
}

module.exports = {
  attach,
  refresh,
  getTranslations,
  t: i18n.t,
  tArray: i18n.tArray,
}
