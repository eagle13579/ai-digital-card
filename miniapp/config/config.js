/**
 * 小程序环境配置
 * AI数智名片 - 开发/生产双模式配置管理
 * =========================================
 * 统一管理所有环境差异项，app.js 和 api.js 统一从此读取。
 *
 * 切换环境方式:
 *   方式1 — 手动修改下方 ENV 变量: 'development' | 'production'
 *   方式2 — 在微信开发者工具「编译模式」中注入 __ENV__ 全局变量
 *   方式3 — 通过 project.config.json 的编译插件或环境变量注入
 */

// ===========================
//  环境开关 — 改这里切换
// ===========================
const ENV = 'development'   // 可选值: 'development' | 'production'

// ===========================
//  各环境配置表
// ===========================
const CONFIGS = {
  development: {
    name: '开发环境',
    apiBaseUrl: 'http://localhost:8002',
    // 调试开关
    debug: true,
    // 是否启用 Mock（无后端时可打开）
    enableMock: false,
  },
  production: {
    name: '生产环境',
    apiBaseUrl: 'https://api.liankebao.top',
    debug: false,
    enableMock: false,
  },
}

// ===========================
//  自动检测覆盖
// ===========================
let effectiveEnv = ENV

// 微信开发者工具注入的 __wxConfig.envVersion
// 'develop' = 开发版, 'trial' = 体验版, 'release' = 正式版
try {
  if (typeof __wxConfig !== 'undefined' && __wxConfig && __wxConfig.envVersion) {
    const wxEnv = __wxConfig.envVersion
    if (wxEnv === 'release') {
      effectiveEnv = 'production'
    } else if (wxEnv === 'trial') {
      // 体验版可指定为生产（带调试），或保留为开发
      effectiveEnv = 'production'
    } else {
      effectiveEnv = 'development'
    }
  }
} catch (e) {
  // __wxConfig 可能不存在（如单元测试环境）
}

// 允许通过全局变量手动覆盖（方便真机调试）
try {
  if (typeof __ENV !== 'undefined' && __ENV) {
    effectiveEnv = __ENV
  }
} catch (e) {
  // ignore
}

// 最终生效配置
const activeConfig = CONFIGS[effectiveEnv] || CONFIGS.development

// 导出
module.exports = {
  ENV: effectiveEnv,
  ...activeConfig,
  // 兼容 apiBaseUrl 命名
  apiBaseUrl: activeConfig.apiBaseUrl,
}
