/**
 * 工具函数集合
 * AI数字名片 - 微信小程序
 */

/**
 * 格式化日期
 * @param {string|Date} date - 日期字符串或Date对象
 * @param {string} fmt - 格式模板，默认 'YYYY-MM-DD'
 * @returns {string}
 */
function formatDate(date, fmt = 'YYYY-MM-DD') {
  if (!date) return ''
  const d = typeof date === 'string' ? new Date(date) : date
  const o = {
    'Y+': d.getFullYear(),
    'M+': d.getMonth() + 1,
    'D+': d.getDate(),
    'H+': d.getHours(),
    'm+': d.getMinutes(),
    's+': d.getSeconds(),
  }
  let result = fmt
  for (const [k, v] of Object.entries(o)) {
    const match = `(${k})`
    const reg = new RegExp(match)
    if (reg.test(result)) {
      result = result.replace(RegExp.$1, String(v).padStart(2, '0'))
    }
  }
  return result
}

/**
 * 格式化相对时间
 * @param {string|Date} date
 * @returns {string}
 */
function formatRelativeTime(date) {
  if (!date) return ''
  const now = Date.now()
  const d = typeof date === 'string' ? new Date(date).getTime() : date.getTime()
  const diff = now - d

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 30) return `${days}天前`
  if (days < 365) return `${Math.floor(days / 30)}个月前`
  return `${Math.floor(days / 365)}年前`
}

/**
 * 脱敏手机号
 * @param {string} phone
 * @returns {string}
 */
function maskPhone(phone) {
  if (!phone || phone.length < 7) return phone || '***'
  return phone.slice(0, 3) + '****' + phone.slice(-4)
}

/**
 * 复制文本到剪贴板
 * @param {string} text
 */
function copyText(text) {
  wx.setClipboardData({
    data: text,
    success() {
      wx.showToast({ title: '已复制', icon: 'success' })
    },
  })
}

/**
 * 显示确认对话框
 * @param {string} title
 * @param {string} content
 * @returns {Promise<boolean>}
 */
function showConfirm(title, content) {
  return new Promise((resolve) => {
    wx.showModal({
      title,
      content,
      success(res) {
        resolve(res.confirm)
      },
    })
  })
}

/**
 * 防抖
 * @param {Function} fn
 * @param {number} delay
 * @returns {Function}
 */
function debounce(fn, delay = 300) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
      timer = null
    }, delay)
  }
}

/**
 * 节流
 * @param {Function} fn
 * @param {number} interval
 * @returns {Function}
 */
function throttle(fn, interval = 500) {
  let last = 0
  return function (...args) {
    const now = Date.now()
    if (now - last >= interval) {
      last = now
      fn.apply(this, args)
    }
  }
}

module.exports = {
  formatDate,
  formatRelativeTime,
  maskPhone,
  copyText,
  showConfirm,
  debounce,
  throttle,
}
