/**
 * 统一API客户端
 *
 * 功能:
 * - 自动携带 token (从 Taro 缓存读取)
 * - 统一错误处理与错误码映射
 * - 超时控制 (15s)
 * - 失败自动重试 (1次)
 * - 提供 get / post / put / del 四个方法
 */

import Taro from '@tarojs/taro'
import { API_BASE_URL, REQUEST_TIMEOUT, REQUEST_RETRY_COUNT } from '../config/env'

/* -------------------------------------------------------------------------- */
/*  类型定义                                                                   */
/* -------------------------------------------------------------------------- */

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

export interface RequestOptions {
  /** 请求方法 */
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  /** 请求体（JSON 对象） */
  data?: Record<string, any>
  /** 自定义请求头（会与默认头部合并） */
  header?: Record<string, string>
  /** 是否不携带 token（默认 false） */
  noAuth?: boolean
  /** 自定义超时（毫秒，默认 15000） */
  timeout?: number
  /** 是否不自动重试（默认 false） */
  noRetry?: boolean
  /** 返回原始响应而非解析后的 data（默认 false） */
  raw?: boolean
}

/* -------------------------------------------------------------------------- */
/*  错误类                                                                     */
/* -------------------------------------------------------------------------- */

export class ApiError extends Error {
  code: number
  constructor(code: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.code = code
  }
}

/* -------------------------------------------------------------------------- */
/*  核心请求方法                                                               */
/* -------------------------------------------------------------------------- */

async function request<T = any>(
  path: string,
  options: RequestOptions = {},
): Promise<ApiResponse<T>> {
  const {
    method = 'GET',
    data,
    header = {},
    noAuth = false,
    timeout = REQUEST_TIMEOUT,
    noRetry = false,
    raw = false,
  } = options

  /* 构建请求头 ------------------------------------------------------------ */
  const defaultHeader: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (!noAuth) {
    try {
      const token = Taro.getStorageSync('token')
      if (token) {
        defaultHeader['Authorization'] = `Bearer ${token}`
      }
    } catch {
      // 静默处理 — 读取缓存失败时不阻塞请求
    }
  }

  const mergedHeader = { ...defaultHeader, ...header }

  /* 发起请求，含重试逻辑 -------------------------------------------------- */
  const maxAttempts = noRetry ? 1 : REQUEST_RETRY_COUNT + 1

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const response = await Taro.request({
        url: `${API_BASE_URL}${path}`,
        method,
        data,
        header: mergedHeader,
        timeout,
      })

      const body = response.data as ApiResponse<T>

      /* 401 统一处理：清除 token 并跳转登录 */
      if (body.code === 401) {
        Taro.removeStorageSync('token')
        Taro.removeStorageSync('user')
        Taro.navigateTo({ url: '/pages/login/index' })
        throw new ApiError(401, body.message || '登录已过期，请重新登录')
      }

      /* token 过期但仍可刷新的场景 */
      if (body.code === 403) {
        throw new ApiError(403, body.message || '权限不足')
      }

      /* 业务错误 — 仍返回响应，让调用方决定是否抛出 */
      if (body.code !== 200 && body.code !== 0) {
        return body
      }

      if (raw) {
        return body
      }

      return body
    } catch (err: any) {
      /* 最后一次尝试 — 抛出异常 */
      if (attempt === maxAttempts) {
        if (err instanceof ApiError) {
          throw err
        }

        const message =
          err.errMsg || err.message || '网络错误，请检查网络连接'

        throw new ApiError(0, message)
      }

      /* 非最后一次 — 短暂延迟后重试 */
      await new Promise((resolve) => setTimeout(resolve, 500))
    }
  }

  /* unreachable */
  throw new ApiError(0, '请求失败')
}

/* -------------------------------------------------------------------------- */
/*  导出便捷方法                                                               */
/* -------------------------------------------------------------------------- */

export const api = {
  /**
   * GET 请求
   * @example api.get('/api/v1/user/profile')
   */
  get<T = any>(path: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return request<T>(path, { ...options, method: 'GET' })
  },

  /**
   * POST 请求
   * @example api.post('/api/auth/login', { phone: '13800138000', password: 'xxx' })
   */
  post<T = any>(
    path: string,
    data?: Record<string, any>,
    options?: RequestOptions,
  ): Promise<ApiResponse<T>> {
    return request<T>(path, { ...options, method: 'POST', data })
  },

  /**
   * PUT 请求
   * @example api.put('/api/user/profile', { name: '新名字' })
   */
  put<T = any>(
    path: string,
    data?: Record<string, any>,
    options?: RequestOptions,
  ): Promise<ApiResponse<T>> {
    return request<T>(path, { ...options, method: 'PUT', data })
  },

  /**
   * DELETE 请求
   * @example api.del('/api/card/123')
   */
  del<T = any>(path: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return request<T>(path, { ...options, method: 'DELETE' })
  },
}

export default api
