/**
 * AI数智名片 — 统一环境配置
 * 所有环境变量集中在此文件，页面/utils通过 require('./config') 读取
 *
 * 使用方式：
 *   const CONFIG = require('./config')
 *   console.log(CONFIG.API_BASE_URL)
 */
const CONFIG = {
  // ===== 环境 =====
  ENV: 'development',   // development | production | testing

  // ===== API =====
  API_BASE_URL: 'https://card.liankebao.top',
  API_TIMEOUT: 15000,   // 15秒（给AI类接口留余量）

  // ===== 功能开关 =====
  USE_REAL_API: true,    // true=调真实后端, false=全Mock
  ENABLE_MOCK_LOGIN: false, // true=免微信授权直接mock登录

  // ===== 缓存 =====
  CACHE_TTL: 5 * 60 * 1000,  // 5分钟
  MAX_CACHE_ENTRIES: 50,

  // ===== 登录 =====
  LOGIN_TIMEOUT: 10000,  // 登录超时10秒
  TOKEN_REFRESH_BEFORE_EXPIRY: 24 * 60 * 60 * 1000, // token过期前24小时预刷新

  // ===== 分页 =====
  DEFAULT_PAGE_SIZE: 20,
}

module.exports = CONFIG
