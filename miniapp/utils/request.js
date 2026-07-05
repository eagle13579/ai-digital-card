/**
 * 统一API请求封装
 * AI数智名片 - 微信小程序
 */

// API baseURL
// 从 app.globalData.apiBaseUrl 读取（由 config/config.js 统一管理）
// 开发环境: http://localhost:8001
// 生产环境: https://api.liankebao.top
let API_BASE_URL = 'http://localhost:8001'  // 默认值，onLaunch 后会被覆盖
try {
  const app = getApp()
  if (app && app.globalData && app.globalData.apiBaseUrl) {
    API_BASE_URL = app.globalData.apiBaseUrl
  }
} catch (e) {
  // app 未初始化时使用默认值
}

// 请求超时时间(ms)
const REQUEST_TIMEOUT = 8000

// 错误码映射
const ERROR_MAP = {
  401: '登录已过期，请重新登录',
  403: '暂无权限访问',
  404: '请求的资源不存在',
  429: '请求过于频繁，请稍后重试',
  500: '服务器繁忙，请稍后重试',
}

/**
 * 发起HTTP请求
 * @param {string} method - 请求方法
 * @param {string} url - 请求路径(相对于baseURL)
 * @param {object} data - 请求体数据
 * @param {object} options - 额外选项
 * @param {boolean} options.noAuth - 是否不需要token
 * @returns {Promise}
 */
function request(method, url, data = {}, options = {}) {
  const app = getApp()
  const token = app.globalData.token
  // 运行时动态获取 apiBaseUrl（确保 onLaunch 写入后生效）
  const baseUrl = app.globalData.apiBaseUrl || 'http://localhost:8001'

  return new Promise((resolve, reject) => {
    // 检查登录态 - 开发模式下跳过
    const app2 = getApp()
    const isDev = app2 && app2.globalData && app2.globalData.__DEV_MODE__
    if (!options.noAuth && !token) {
      if (isDev) {
        // 开发模式: 放行请求, 后端会返回401, 由调用方catch处理
        console.warn('[API] 开发模式: 未登录, 尝试请求后端...')
      } else {
        wx.showToast({ title: '请先登录', icon: 'none' })
        reject(new Error('未登录'))
        return
      }
    }

    const header = {
      'Content-Type': 'application/json',
    }
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.request({
      url: `${baseUrl}${url}`,
      method,
      header,
      data,
      timeout: REQUEST_TIMEOUT,
      success(res) {
        const { statusCode, data: resData } = res

        if (statusCode >= 200 && statusCode < 300) {
          resolve(resData)
        } else if (statusCode === 401) {
          // token过期，清除登录态
          app.clearLogin()
          wx.showToast({ title: '登录已过期', icon: 'none' })
          reject(resData)
        } else {
          const errorMsg = ERROR_MAP[statusCode] || resData?.detail || '请求失败'
          wx.showToast({ title: errorMsg, icon: 'none' })
          reject(resData)
        }
      },
      fail(err) {
        const errMsg = err.errMsg || '网络连接失败，请检查网络'
        wx.showToast({ title: errMsg, icon: 'none' })
        reject(err)
      },
    })
  })
}

/**
 * GET 请求
 */
function get(url, data = {}, options = {}) {
  return request('GET', url, data, options)
}

/**
 * POST 请求
 */
function post(url, data = {}, options = {}) {
  return request('POST', url, data, options)
}

/**
 * PUT 请求
 */
function put(url, data = {}, options = {}) {
  return request('PUT', url, data, options)
}

/**
 * DELETE 请求
 */
function del(url, data = {}, options = {}) {
  return request('DELETE', url, data, options)
}

module.exports = {
  get,
  post,
  put,
  del,
  request,
  API_BASE_URL,
}
