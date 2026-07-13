/**
 * 调试工具函数
 * AI数智名片 - 微信小程序
 * 
 * 提供开发/调试辅助函数，仅开发环境生效
 */

const isDev = (function() {
  try {
    const accountInfo = wx.getAccountInfoSync()
    // 开发版或体验版视为开发环境
    return accountInfo.miniProgram.envVersion === 'develop'
      || accountInfo.miniProgram.envVersion === 'trial'
  } catch (e) {
    return false
  }
})()

/**
 * 条件性打印日志（仅开发环境输出）
 * @param {...any} args - 传递给 console.log 的参数
 */
function log(...args) {
  if (!isDev) return
  const timestamp = new Date().toLocaleTimeString()
  console.log(`[DEBUG ${timestamp}]`, ...args)
}

/**
 * 条件性打印警告（仅开发环境输出）
 * @param {...any} args - 传递给 console.warn 的参数
 */
function warn(...args) {
  if (!isDev) return
  const timestamp = new Date().toLocaleTimeString()
  console.warn(`[DEBUG ${timestamp}]`, ...args)
}

/**
 * 条件性打印错误（生产环境也输出，加前缀便于检索）
 * @param {...any} args - 传递给 console.error 的参数
 */
function error(...args) {
  const timestamp = new Date().toLocaleTimeString()
  console.error(`[ERROR ${timestamp}]`, ...args)
}

/**
 * 检查对象是否为空（{}）
 * @param {object} obj
 * @returns {boolean}
 */
function isEmptyObject(obj) {
  return obj && typeof obj === 'object' && !Array.isArray(obj)
    && Object.keys(obj).length === 0
}

/**
 * 安全 JSON 解析，解析失败返回 fallback
 * @param {string} str - 要解析的 JSON 字符串
 * @param {*} fallback - 解析失败时返回的默认值
 * @returns {*}
 */
function safeParseJSON(str, fallback = null) {
  try {
    return JSON.parse(str)
  } catch (e) {
    return fallback
  }
}

/**
 * 计算函数执行耗时（仅开发环境打印）
 * @param {string} label - 耗时标签
 * @param {Function} fn - 要执行的函数
 * @returns {*} 函数执行结果
 */
function time(label, fn) {
  if (!isDev) return fn()
  const start = Date.now()
  const result = fn()
  const elapsed = Date.now() - start
  console.log(`[PERF] ${label}: ${elapsed}ms`)
  return result
}

/**
 * 异步函数执行耗时
 * @param {string} label - 耗时标签
 * @param {Function} asyncFn - 要执行的异步函数
 * @returns {Promise<*>} 函数执行结果
 */
async function timeAsync(label, asyncFn) {
  if (!isDev) return asyncFn()
  const start = Date.now()
  const result = await asyncFn()
  const elapsed = Date.now() - start
  console.log(`[PERF] ${label}: ${elapsed}ms`)
  return result
}

/**
 * 获取 Storage 使用情况统计（调试用）
 * @returns {object} 各 key 的大小和总大小
 */
function getStorageStats() {
  try {
    const info = wx.getStorageInfoSync()
    const stats = {
      totalKeys: info.keys.length,
      currentSize: `${(info.currentSize / 1024).toFixed(2)} KB`,
      limitSize: `${(info.limitSize / 1024).toFixed(2)} KB`,
      usage: `${((info.currentSize / info.limitSize) * 100).toFixed(1)}%`,
      keys: info.keys,
    }
    return stats
  } catch (e) {
    return { error: e.message }
  }
}

/**
 * 页面数据快照（调试用，打印当前页面 data）
 */
function snapshot(pageInstance, label = 'Page Data') {
  if (!isDev) return
  try {
    const data = JSON.parse(JSON.stringify(pageInstance.data || {}))
    console.log(`[SNAPSHOT] ${label}:`, data)
  } catch (e) {
    console.warn('[SNAPSHOT] 序列化失败:', e.message)
  }
}

module.exports = {
  isDev,
  log,
  warn,
  error,
  isEmptyObject,
  safeParseJSON,
  time,
  timeAsync,
  getStorageStats,
  snapshot,
}
