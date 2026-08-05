/**
 * 离线数据缓存层 (PWA级)
 * AI数智名片 - 微信小程序
 * 
 * 封装 wx.setStorage / wx.getStorage，支持：
 * - 过期时间（TTL）
 * - 网络状态检测与监听
 * - 缓存优先策略（stale-while-revalidate）
 * - 网络优先策略（network-first，失败回退缓存）
 * - 自动缓存键前缀，避免命名冲突
 */
const CACHE_PREFIX = 'ai_card_cache_'
const DEFAULT_TTL = 5 * 60 * 1000 // 默认5分钟
const NETWORK_KEY = 'ai_card_network_state'

// ===== 网络状态管理 =====

let _networkType = 'unknown'
let _isOnline = true
const _networkListeners = []

/**
 * 初始化网络监听（在 app.js onLaunch 中调用）
 */
function initNetworkListener() {
  // 获取当前网络状态
  wx.getNetworkType({
    success(res) {
      _networkType = res.networkType
      _isOnline = res.networkType !== 'none'
      console.log('[Cache] 当前网络:', _networkType, '在线:', _isOnline)
      // 持久化到全局 storage 供其他模块读取
      wx.setStorageSync(NETWORK_KEY, { networkType: _networkType, isOnline: _isOnline })
    },
    fail() {
      _isOnline = false
    },
  })

  // 监听网络变化
  wx.onNetworkStatusChange((res) => {
    const prevOnline = _isOnline
    _networkType = res.networkType
    _isOnline = res.isConnected
    console.log('[Cache] 网络状态变化:', _networkType, '在线:', _isOnline)

    // 持久化最新状态
    wx.setStorageSync(NETWORK_KEY, { networkType: _networkType, isOnline: _isOnline })

    // 通知所有监听者
    _networkListeners.forEach(fn => {
      try {
        fn({ networkType: _networkType, isConnected: _isOnline, fromOffline: !prevOnline && _isOnline })
      } catch (e) {
        console.warn('[Cache] listener error:', e)
      }
    })
  })
}

/**
 * 检测当前是否在线
 * @returns {boolean}
 */
function isOnline() {
  return _isOnline
}

/**
 * 获取当前网络类型（wifi/4g/3g/2g/none/unknown）
 * @returns {string}
 */
function getNetworkType() {
  return _networkType
}

/**
 * 订阅网络状态变化
 * @param {Function} fn - 回调 (state: { networkType, isConnected, fromOffline })
 * @returns {Function} 取消订阅函数
 */
function onNetworkChange(fn) {
  _networkListeners.push(fn)
  return () => {
    const idx = _networkListeners.indexOf(fn)
    if (idx > -1) _networkListeners.splice(idx, 1)
  }
}

/**
 * 读取持久化的网络状态（供 request.js 等模块同步获取）
 * @returns {{ networkType: string, isOnline: boolean }}
 */
function getStoredNetworkState() {
  try {
    const state = wx.getStorageSync(NETWORK_KEY)
    return state || { networkType: 'unknown', isOnline: true }
  } catch (e) {
    return { networkType: 'unknown', isOnline: true }
  }
}

// ===== 缓存管理 =====

/**
 * 生成带前缀的缓存键
 */
function _getKey(key) {
  return CACHE_PREFIX + key
}

/**
 * 从缓存读取数据
 * @param {string} key - 缓存键
 * @param {object} [options]
 * @param {number} [options.ttl] - 过期时间(ms)，默认 DEFAULT_TTL
 * @param {boolean} [options.ignoreExpiry] - 是否忽略过期（离线时使用）
 * @returns {any|null} 命中则返回数据，否则返回 null
 */
function get(key, options = {}) {
  const { ttl = DEFAULT_TTL, ignoreExpiry = false } = options
  try {
    const raw = wx.getStorageSync(_getKey(key))
    if (!raw) return null

    const item = typeof raw === 'string' ? JSON.parse(raw) : raw

    // 校验格式
    if (!item || !item.data || !item._cachedAt) return null

    // 检查是否过期
    if (!ignoreExpiry) {
      const elapsed = Date.now() - item._cachedAt
      if (elapsed > (item._ttl || ttl)) {
        // 过期，自动清理
        wx.removeStorageSync(_getKey(key))
        console.log('[Cache] key 已过期, 已清除:', key)
        return null
      }
    }

    return item.data
  } catch (e) {
    console.warn('[Cache] get 错误:', key, e)
    return null
  }
}

/**
 * 写入缓存
 * @param {string} key - 缓存键
 * @param {any} data - 要缓存的数据
 * @param {object} [options]
 * @param {number} [options.ttl] - 过期时间(ms)
 * @returns {boolean} 是否成功
 */
function set(key, data, options = {}) {
  try {
    const item = {
      data,
      _cachedAt: Date.now(),
      _ttl: options.ttl || DEFAULT_TTL,
    }
    wx.setStorageSync(_getKey(key), item)
    return true
  } catch (e) {
    console.warn('[Cache] set 错误:', key, e)
    // Storage 可能已满，尝试清旧缓存
    if (e.errMsg && e.errMsg.indexOf('exceed') > -1) {
      _cleanupOldest()
      try {
        wx.setStorageSync(_getKey(key), { data, _cachedAt: Date.now(), _ttl: options.ttl || DEFAULT_TTL })
        return true
      } catch (e2) {
        console.warn('[Cache] 清理后仍写入失败:', key, e2)
      }
    }
    return false
  }
}

/**
 * 删除缓存
 * @param {string} key
 * @returns {boolean}
 */
function remove(key) {
  try {
    wx.removeStorageSync(_getKey(key))
    return true
  } catch (e) {
    return false
  }
}

/**
 * 清空所有本模块的缓存
 * @returns {boolean}
 */
function clear() {
  try {
    const info = wx.getStorageInfoSync()
    info.keys.forEach(k => {
      if (k.startsWith(CACHE_PREFIX)) {
        wx.removeStorageSync(k)
      }
    })
    return true
  } catch (e) {
    return false
  }
}

/**
 * 获取缓存信息
 * @returns {{ totalKeys: number, cacheKeys: number, currentSize: number, limitSize: number }|null}
 */
function info() {
  try {
    const storageInfo = wx.getStorageInfoSync()
    const cacheKeys = storageInfo.keys.filter(k => k.startsWith(CACHE_PREFIX))
    return {
      totalKeys: storageInfo.keys.length,
      cacheKeys: cacheKeys.length,
      currentSize: storageInfo.currentSize,
      limitSize: storageInfo.limitSize,
    }
  } catch (e) {
    return null
  }
}

/**
 * 清理最旧的缓存项（Storage 满时自动调用）
 */
function _cleanupOldest() {
  try {
    const info = wx.getStorageInfoSync()
    const cacheKeys = info.keys.filter(k => k.startsWith(CACHE_PREFIX))

    // 读取所有缓存项的缓存时间
    const items = cacheKeys.map(k => {
      try {
        const raw = wx.getStorageSync(k)
        const item = typeof raw === 'string' ? JSON.parse(raw) : raw
        return { key: k, cachedAt: item._cachedAt || 0 }
      } catch (e) {
        return { key: k, cachedAt: 0 }
      }
    })

    // 按缓存时间升序排列（最旧在前）
    items.sort((a, b) => a.cachedAt - b.cachedAt)

    // 删除最旧的 20%
    const removeCount = Math.max(1, Math.floor(items.length * 0.2))
    items.slice(0, removeCount).forEach(item => {
      wx.removeStorageSync(item.key)
    })
    console.log('[Cache] Storage 满，已清理', removeCount, '个最旧缓存')
  } catch (e) {
    console.warn('[Cache] 清理失败:', e)
  }
}

// ===== 缓存策略 =====

/**
 * 缓存优先策略：先返回缓存（如果有），再异步刷新
 * 「stale-while-revalidate」模式
 * 
 * @param {string} cacheKey - 缓存键
 * @param {Function} fetchFn - 异步获取数据的函数 () => Promise<data>
 * @param {object} [options]
 * @param {number} [options.ttl] - 缓存过期时间(ms)
 * @param {boolean} [options.skipCache] - 是否跳过缓存强制请求
 * @returns {Promise<any>}
 */
async function cacheFirst(cacheKey, fetchFn, options = {}) {
  const { ttl = DEFAULT_TTL, skipCache = false } = options

  // 跳过缓存标记（如强制刷新）
  if (!skipCache) {
    if (isOnline()) {
      // 在线：正常TTL检查，命中则返回 + 后台刷新
      const cached = get(cacheKey, { ttl, ignoreExpiry: false })
      if (cached !== null) {
        console.log('[Cache] cacheFirst 命中缓存:', cacheKey)
        // 后台静默刷新
        fetchFn()
          .then(data => {
            if (data !== undefined && data !== null) {
              set(cacheKey, data, { ttl })
              console.log('[Cache] cacheFirst 后台刷新完成:', cacheKey)
            }
          })
          .catch(() => {
            // 静默失败，不影响用户
          })
        return cached
      }
    } else {
      // 离线：忽略过期，尽量返回
      const cached = get(cacheKey, { ignoreExpiry: true })
      if (cached !== null) {
        console.log('[Cache] cacheFirst 离线命中缓存:', cacheKey)
        return cached
      }
    }
  }

  // 无缓存 → 正常请求
  try {
    const data = await fetchFn()
    if (data !== undefined && data !== null) {
      set(cacheKey, data, { ttl })
    }
    return data
  } catch (e) {
    // 请求失败 → 尝试读取过期缓存（最后手段）
    console.warn('[Cache] cacheFirst 请求失败，尝试过期缓存:', cacheKey, e)
    const stale = get(cacheKey, { ignoreExpiry: true })
    if (stale !== null) return stale
    throw e
  }
}

/**
 * 网络优先策略：先请求网络，失败时回退到缓存
 * @param {string} cacheKey - 缓存键
 * @param {Function} fetchFn - 异步获取数据的函数 () => Promise<data>
 * @param {object} [options]
 * @param {number} [options.ttl] - 缓存过期时间(ms)
 * @returns {Promise<any>}
 */
async function networkFirst(cacheKey, fetchFn, options = {}) {
  const { ttl = DEFAULT_TTL } = options

  try {
    const data = await fetchFn()
    if (data !== undefined && data !== null) {
      set(cacheKey, data, { ttl })
    }
    return data
  } catch (e) {
    // 网络失败 → 回退到缓存
    console.warn('[Cache] networkFirst 回退到缓存:', cacheKey, e)
    const cached = get(cacheKey, { ignoreExpiry: true })
    if (cached !== null) return cached
    throw e
  }
}

module.exports = {
  // 网络状态
  initNetworkListener,
  isOnline,
  getNetworkType,
  onNetworkChange,
  getStoredNetworkState,
  // 缓存管理
  get,
  set,
  remove,
  clear,
  info,
  // 策略
  cacheFirst,
  networkFirst,
  // 常量
  CACHE_PREFIX,
  DEFAULT_TTL,
}
