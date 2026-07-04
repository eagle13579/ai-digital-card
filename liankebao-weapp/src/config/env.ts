/**
 * 环境变量配置
 *
 * 生产环境: https://liankebao.top/lkapi
 * 开发环境: http://localhost:8001 (WSL后端)
 *
 * 构建时可通过 TARO_APP_API_BASE_URL 环境变量覆盖
 */

const PROD_API_BASE = 'https://liankebao.top/lkapi'
const DEV_API_BASE = 'http://localhost:8001'

/** 当前是否为开发模式 */
export const IS_DEV = process.env.NODE_ENV === 'development'

/** 后端API基础地址 */
export const API_BASE_URL: string = IS_DEV ? DEV_API_BASE : PROD_API_BASE

/** 请求超时时间（毫秒） */
export const REQUEST_TIMEOUT = 15000

/** 请求重试次数 */
export const REQUEST_RETRY_COUNT = 1
