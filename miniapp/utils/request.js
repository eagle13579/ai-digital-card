/**
 * 统一API请求封装
 * AI数智名片 - 微信小程序
 * 
 * 设计说明（参考 F06_API统一响应格式.feature.md）：
 * - 所有响应遵循 { code, message, data } 三字段格式
 * - 自动注入 Bearer Token（从 store 读取）
 * - 401 自动清除登录态并跳转登录页
 * - 非 0 code 自动 Toast 错误信息
 */

const store = require('./store')

// API baseURL
// 微信小程序API基础URL — 全部走生产域名（后端已部署到服务器）
const PROD_API = 'https://card.liankebao.top'

const API_BASE_URL = (function() {
  // 开发工具/体验版/正式版统一使用生产域名
  // 后端部署在阿里云服务器，不需要本地开发环境
  return PROD_API
})()

// 请求超时时间(ms)
const REQUEST_TIMEOUT = 15000

// HTTP状态码 → 用户提示
const HTTP_ERROR_MAP = {
  400: '请求参数错误',
  401: '登录已过期，请重新登录',
  403: '暂无权限访问',
  404: '请求的资源不存在',
  429: '请求过于频繁，请稍后重试',
  500: '服务器繁忙，请稍后重试',
  502: '网关错误',
  503: '服务暂不可用',
}

/**
 * 发起HTTP请求
 * @param {string} method - 请求方法 (GET/POST/PUT/DELETE)
 * @param {string} url - 请求路径（相对于 baseURL）
 * @param {object} data - 请求体数据（GET时为 query params）
 * @param {object} options - 额外选项
 * @param {boolean} options.noAuth - 是否不需要token（默认 false）
 * @param {boolean} options.noToast - 是否不自动弹Toast（默认 false）
 * @returns {Promise<any>} 成功时直接返回 data 字段
 */
function request(method, url, data = {}, options = {}) {
  const { token } = store.getState()

  return new Promise((resolve, reject) => {
    // 检查登录态
    if (!options.noAuth && !token) {
      const err = new Error('未登录')
      if (!options.noToast) {
        wx.showToast({ title: '请先登录', icon: 'none' })
      }
      reject(err)
      return
    }

    // 构建请求头
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
        const { statusCode, data: body } = res

        // ---- HTTP 层成功 ----
        if (statusCode >= 200 && statusCode < 300) {
          // 统一响应格式: { code, message, data }
          if (body && typeof body === 'object' && 'code' in body) {
            if (body.code === 0) {
              // ✅ 业务成功 → 直接返回 data
              resolve(body.data !== undefined ? body.data : body)
            } else {
              // ❌ 业务错误 → Toast 错误信息
              const errMsg = body.message || '请求失败'
              if (!options.noToast) {
                wx.showToast({ title: errMsg, icon: 'none' })
              }
              reject(body)
            }
          } else {
            // 非标准格式（旧接口兼容），直接返回
            resolve(body)
          }
          return
        }

        // ---- HTTP 层失败 ----
        if (statusCode === 401) {
          // Token 过期 → 清除登录态 → 跳转登录页
          store.logout()
          if (!options.noToast) {
            wx.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
          }
          reject(body || { code: 401, message: '登录已过期' })
        } else {
          const errMsg = HTTP_ERROR_MAP[statusCode]
            || (body && body.message)
            || (body && body.detail)
            || '请求失败'
          if (!options.noToast) {
            wx.showToast({ title: errMsg, icon: 'none' })
          }
          reject(body || { code: statusCode, message: errMsg })
        }
      },
      fail(err) {
        // 网络层失败（断网、超时、DNS解析失败）
        const errMsg = err.errMsg || '网络连接失败，请检查网络'
        if (!options.noToast) {
          wx.showToast({ title: errMsg, icon: 'none' })
        }
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

/**
 * 文件上传（封装 wx.uploadFile，统一走 request.js 的认证与错误处理）
 * @param {string} url - 上传路径（相对于 API_BASE_URL）
 * @param {string} filePath - 文件本地临时路径
 * @param {string} name - 文件字段名（后端接收的 key）
 * @param {object} formData - 额外的表单数据
 * @param {object} options - 额外选项
 * @param {boolean} options.noAuth - 是否不传 token（默认 false）
 * @param {boolean} options.noToast - 是否不自动弹 Toast（默认 false）
 * @returns {Promise<any>}
 */
function upload(url, filePath, name = 'file', formData = {}, options = {}) {
  const { token } = store.getState()

  return new Promise((resolve, reject) => {
    if (!options.noAuth && !token) {
      const err = new Error('未登录')
      if (!options.noToast) {
        wx.showToast({ title: '请先登录', icon: 'none' })
      }
      reject(err)
      return
    }

    const header = {}
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.uploadFile({
      url: `${API_BASE_URL}${url}`,
      filePath,
      name,
      formData,
      header,
      success(res) {
        const { statusCode, data: bodyStr } = res
        let body
        try {
          body = typeof bodyStr === 'string' ? JSON.parse(bodyStr) : bodyStr
        } catch (e) {
          body = { raw: bodyStr }
        }

        if (statusCode >= 200 && statusCode < 300) {
          // 统一响应格式: { code, message, data }
          if (body && typeof body === 'object' && 'code' in body) {
            if (body.code === 0) {
              resolve(body.data !== undefined ? body.data : body)
            } else {
              const errMsg = body.message || '上传失败'
              if (!options.noToast) {
                wx.showToast({ title: errMsg, icon: 'none' })
              }
              reject(body)
            }
          } else {
            // 非标准格式，直接返回
            resolve(body)
          }
        } else {
          const errMsg = HTTP_ERROR_MAP[statusCode] || '上传失败'
          if (!options.noToast) {
            wx.showToast({ title: errMsg, icon: 'none' })
          }
          reject(body || { code: statusCode, message: errMsg })
        }
      },
      fail(err) {
        const errMsg = err.errMsg || '网络连接失败，请检查网络'
        if (!options.noToast) {
          wx.showToast({ title: errMsg, icon: 'none' })
        }
        reject(err)
      },
    })
  })
}

module.exports = {
  get,
  post,
  put,
  del,
  request,
  upload,
  API_BASE_URL,
}
