/**
 * 统一API请求封装
 * AI数字名片 - 微信小程序
 */

// API baseURL
// 微信小程序API基础URL — 自动检测环境
// 开发工具中用本机IP，真机调试用实际服务器地址
const API_BASE_URL = (function() {
  // 微信开发者工具中可以用 localhost 或本机IP
  // 真机/预览时必须用实际IP或域名
  const DEV_IP = '192.168.7.48'   // 后端服务器IP
  const DEV_PORT = '8201'          // AI数字名片后端端口
  
  // __wxConfig 是微信开发者工具注入的全局变量
  try {
    if (typeof __wxConfig !== 'undefined' && __wxConfig && __wxConfig.envVersion === 'develop') {
      return `http://${DEV_IP}:${DEV_PORT}`
    }
  } catch(e) {}
  return `http://${DEV_IP}:${DEV_PORT}`
})()

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

  return new Promise((resolve, reject) => {
    // 检查登录态
    if (!options.noAuth && !token) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      reject(new Error('未登录'))
      return
    }

    const header = {
      'Content-Type': 'application/json',
    }
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.request({
      url: `${API_BASE_URL}${url}`,
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
