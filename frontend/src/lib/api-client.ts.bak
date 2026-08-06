/**
 * AI数字名片 - 基础 API 客户端
 *
 * TypeScript 类型安全的 HTTP 客户端。
 * 作为 SDK 生成前的过渡方案，提供 fetch 封装 + 自动重试 + 统一错误处理。
 *
 * 使用方式:
 *   import { apiClient } from '@/lib/api-client';
 *
 *   // GET
 *   const brochures = await apiClient.get<Brochure[]>('/api/brochures');
 *
 *   // POST with body
 *   const result = await apiClient.post<ApiResponse>('/api/auth/login', { phone, password });
 *
 *   // With options
 *   const data = await apiClient.get<Brochure>('/api/brochures/123', {
 *     retries: 3,
 *     timeout: 10000,
 *   });
 *
 * 当 SDK 生成完成后，可以无缝切换:
 *   import { BrochuresApi } from '@/lib/api-sdk';
 *   const api = new BrochuresApi();
 *   const brochures = await api.listBrochures();
 */

// ─── 类型定义 ─────────────────────────────────────────────────────────────────

/** API 统一响应格式 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data?: T;
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** 分页请求参数 */
export interface PaginationParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

/** 请求配置 */
export interface ClientOptions {
  /** 基础 URL，默认从环境变量或空字符串（通过 Nginx 代理） */
  baseURL?: string;
  /** 超时时间（毫秒），默认 15000 */
  timeout?: number;
  /** 最大重试次数，默认 2 */
  retries?: number;
  /** 重试间隔（毫秒），默认 1000 */
  retryDelay?: number;
  /** 自定义请求头 */
  headers?: Record<string, string>;
  /** token 持久化 key */
  tokenKey?: string;
  /** 日志级别 */
  logLevel?: 'none' | 'error' | 'warn' | 'info';
}

/** 单次请求选项（覆盖 ClientOptions） */
export interface RequestOptions extends Pick<ClientOptions, 'timeout' | 'retries' | 'retryDelay' | 'logLevel'> {
  /** 是否跳过 token 自动注入 */
  skipAuth?: boolean;
  /** 是否返回原始 Response（跳过 JSON 解析） */
  rawResponse?: boolean;
  /** 请求信号（用于取消） */
  signal?: AbortSignal;
}

/** API 错误 */
export class ApiError extends Error {
  public readonly code: number;
  public readonly status: number;
  public readonly data?: unknown;

  constructor(status: number, code: number, message: string, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.data = data;
  }
}

/** 网络错误 */
export class NetworkError extends Error {
  public readonly cause?: unknown;

  constructor(message: string, cause?: unknown) {
    super(message);
    this.name = 'NetworkError';
    this.cause = cause;
  }
}

/** 超时错误 */
export class TimeoutError extends Error {
  constructor(timeout: number) {
    super(`请求超时 (${timeout}ms)`);
    this.name = 'TimeoutError';
  }
}

// ─── 请求拦截器接口 ───────────────────────────────────────────────────────────

export interface RequestInterceptor {
  /** 在请求发送前修改配置 */
  onRequest?: (url: string, init: RequestInit) => { url: string; init: RequestInit } | Promise<{ url: string; init: RequestInit }>;
  /** 在请求出错时处理 */
  onError?: (error: Error) => Error | Promise<Error>;
}

export interface ResponseInterceptor {
  /** 在响应返回后处理数据 */
  onResponse?: <T>(response: Response, data: T) => T | Promise<T>;
  /** 在响应出错时处理 */
  onError?: (error: ApiError) => ApiError | Promise<ApiError>;
}

// ─── 默认配置 ─────────────────────────────────────────────────────────────────

const DEFAULT_OPTIONS: Required<ClientOptions> = {
  baseURL: '',
  timeout: 15000,
  retries: 2,
  retryDelay: 1000,
  headers: {},
  tokenKey: 'token',
  logLevel: 'error',
};

// ─── 核心客户端 ───────────────────────────────────────────────────────────────

class ApiClient {
  private config: Required<ClientOptions>;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];

  constructor(options?: ClientOptions) {
    this.config = { ...DEFAULT_OPTIONS, ...options };
  }

  // ── 配置 ──

  /** 更新全局配置 */
  configure(options: Partial<ClientOptions>): void {
    this.config = { ...this.config, ...options };
  }

  /** 获取当前配置 */
  getConfig(): Readonly<Required<ClientOptions>> {
    return { ...this.config };
  }

  // ── Token 管理 ──

  /** 获取 token */
  getToken(): string | null {
    try {
      return localStorage.getItem(this.config.tokenKey);
    } catch {
      return null;
    }
  }

  /** 保存 token */
  setToken(token: string): void {
    try {
      localStorage.setItem(this.config.tokenKey, token);
    } catch {
      this.log('warn', '无法保存 token: localStorage 不可用');
    }
  }

  /** 清除 token */
  clearToken(): void {
    try {
      localStorage.removeItem(this.config.tokenKey);
    } catch {
      // ignore
    }
  }

  // ── 拦截器 ──

  /** 注册请求拦截器 */
  addRequestInterceptor(interceptor: RequestInterceptor): () => void {
    this.requestInterceptors.push(interceptor);
    return () => {
      this.requestInterceptors = this.requestInterceptors.filter(i => i !== interceptor);
    };
  }

  /** 注册响应拦截器 */
  addResponseInterceptor(interceptor: ResponseInterceptor): () => void {
    this.responseInterceptors.push(interceptor);
    return () => {
      this.responseInterceptors = this.responseInterceptors.filter(i => i !== interceptor);
    };
  }

  // ── 公共 HTTP 方法 ──

  /** GET 请求 */
  async get<T = unknown>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('GET', path, undefined, options);
  }

  /** POST 请求 */
  async post<T = unknown>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('POST', path, body, options);
  }

  /** PUT 请求 */
  async put<T = unknown>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('PUT', path, body, options);
  }

  /** PATCH 请求 */
  async patch<T = unknown>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('PATCH', path, body, options);
  }

  /** DELETE 请求 */
  async delete<T = unknown>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('DELETE', path, undefined, options);
  }

  /** 上传文件（FormData） */
  async upload<T = unknown>(path: string, formData: FormData, options?: RequestOptions): Promise<T> {
    return this.request<T>('POST', path, formData, { ...options, skipAuth: false });
  }

  /** 下载文件 */
  async download(path: string, options?: RequestOptions): Promise<Blob> {
    const response = await this.rawRequest('GET', path, undefined, options);
    return response.blob();
  }

  // ── 核心请求方法 ──

  /**
   * 发起 HTTP 请求（自动重试 + 错误处理）
   */
  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options?: RequestOptions,
  ): Promise<T> {
    const response = await this.rawRequest(method, path, body, options);

    if (options?.rawResponse) {
      return response as unknown as T;
    }

    // 解析 JSON
    let data: T;
    try {
      data = await response.json();
    } catch {
      const text = await response.text().catch(() => '');
      throw new ApiError(
        response.status,
        -1,
        `响应不是有效的 JSON: ${text.slice(0, 100)}`,
      );
    }

    // 应用响应拦截器
    for (const interceptor of this.responseInterceptors) {
      if (interceptor.onResponse) {
        data = await interceptor.onResponse(response, data);
      }
    }

    return data;
  }

  /**
   * 发起原始请求（带重试逻辑）
   */
  private async rawRequest(
    method: string,
    path: string,
    body?: unknown,
    options?: RequestOptions,
  ): Promise<Response> {
    const retries = options?.retries ?? this.config.retries;
    const retryDelay = options?.retryDelay ?? this.config.retryDelay;
    const timeout = options?.timeout ?? this.config.timeout;
    const logLevel = options?.logLevel ?? this.config.logLevel;

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        // 延迟重试
        if (attempt > 0) {
          const delay = retryDelay * Math.pow(2, attempt - 1); // 指数退避
          this.log('info', `重试 ${attempt}/${retries}，等待 ${delay}ms...`);
          await sleep(delay);
        }

        return await this.executeRequest(method, path, body, timeout, options);
      } catch (err) {
        lastError = err as Error;

        // 是否可重试的判断
        const shouldRetry = attempt < retries && isRetryableError(err);

        if (shouldRetry) {
          this.log('warn', `请求失败 (尝试 ${attempt + 1}/${retries + 1}): ${lastError.message}`);
          continue;
        }

        // 应用错误拦截器
        let processedError = lastError;
        for (const interceptor of this.responseInterceptors) {
          if (interceptor.onError && processedError instanceof ApiError) {
            processedError = await interceptor.onError(processedError);
          }
        }
        for (const interceptor of this.requestInterceptors) {
          if (interceptor.onError) {
            processedError = await interceptor.onError(processedError);
          }
        }

        throw processedError;
      }
    }

    // 不应到达这里，但为了类型安全
    throw lastError ?? new Error('未知请求错误');
  }

  /**
   * 执行单次 HTTP 请求
   */
  private async executeRequest(
    method: string,
    path: string,
    body: unknown,
    timeout: number,
    options?: RequestOptions,
  ): Promise<Response> {
    const url = `${this.config.baseURL}${path}`;

    // 构建请求头
    const headers: Record<string, string> = {
      ...this.config.headers,
    };

    // 自动注入 Content-Type（FormData 除外）
    if (!(body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    // 自动注入 token
    if (!options?.skipAuth) {
      const token = this.getToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    // 构建请求体
    let initBody: BodyInit | undefined;
    if (body !== undefined && body !== null) {
      initBody = body instanceof FormData ? body : JSON.stringify(body);
    }

    // 构建 RequestInit
    let init: RequestInit = {
      method,
      headers,
      body: initBody,
      signal: options?.signal,
    };

    // 应用请求拦截器
    let finalUrl = url;
    let finalInit = init;
    for (const interceptor of this.requestInterceptors) {
      if (interceptor.onRequest) {
        const result = await interceptor.onRequest(finalUrl, finalInit);
        finalUrl = result.url;
        finalInit = result.init;
      }
    }

    // 创建 AbortController（如果没提供 signal）
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    const signal = finalInit.signal
      ? anySignal(finalInit.signal, controller.signal)
      : controller.signal;

    this.log('info', `${method} ${finalUrl}`);

    try {
      const response = await fetch(finalUrl, {
        ...finalInit,
        signal,
      });

      // 处理 HTTP 错误状态
      if (!response.ok) {
        let errorData: unknown;
        try {
          errorData = await response.json().catch(() => null);
        } catch {
          // ignore
        }

        const apiError = new ApiError(
          response.status,
          (errorData as any)?.code ?? response.status,
          (errorData as any)?.message ?? `HTTP ${response.status}: ${response.statusText}`,
          errorData,
        );

        // Token 过期，清除 token
        if (response.status === 401) {
          this.clearToken();
        }

        throw apiError;
      }

      return response;
    } catch (err) {
      // 处理 AbortError
      if (err instanceof DOMException && err.name === 'AbortError') {
        throw new TimeoutError(timeout);
      }
      // 处理网络错误
      if (err instanceof TypeError && err.message === 'Failed to fetch') {
        throw new NetworkError('网络连接失败，请检查网络', err);
      }
      throw err;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // ── 日志 ──

  private log(level: 'info' | 'warn' | 'error', message: string): void {
    const levels = { none: 0, error: 1, warn: 2, info: 3 };
    if (levels[level] <= levels[this.config.logLevel]) {
      const prefix = '[API Client]';
      switch (level) {
        case 'info':
          console.info(`${prefix} ${message}`);
          break;
        case 'warn':
          console.warn(`${prefix} ${message}`);
          break;
        case 'error':
          console.error(`${prefix} ${message}`);
          break;
      }
    }
  }
}

// ─── 工具函数 ─────────────────────────────────────────────────────────────────

/** 延迟指定毫秒 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/** 判断错误是否可重试 */
function isRetryableError(err: unknown): boolean {
  if (err instanceof TimeoutError) return true;
  if (err instanceof NetworkError) return true;
  if (err instanceof ApiError) {
    // 5xx 可重试，4xx 不可重试（除 429）
    return err.status >= 500 || err.status === 429;
  }
  return false;
}

/** 合并多个 AbortSignal */
function anySignal(...signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController();

  const onAbort = () => {
    controller.abort();
    for (const signal of signals) {
      signal.removeEventListener('abort', onAbort);
    }
  };

  for (const signal of signals) {
    if (signal.aborted) {
      onAbort();
      break;
    }
    signal.addEventListener('abort', onAbort);
  }

  return controller.signal;
}

// ─── 单例导出 ─────────────────────────────────────────────────────────────────

/**
 * 全局 API 客户端实例。
 * 优先使用环境变量 VITE_API_BASE_URL 设置基础 URL。
 */
/**
 * 从 Vite 环境变量获取配置（运行时安全）。
 * Vite 会在构建时替换 import.meta.env，TypeScript 需要 vite/client 类型。
 * 参考: frontend/src/vite-env.d.ts
 */
// @ts-ignore - import.meta.env 由 Vite 提供类型定义
const VITE_API_BASE_URL = typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL;
// @ts-ignore
const VITE_API_LOG_LEVEL = typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_LOG_LEVEL;

export const apiClient = new ApiClient({
  baseURL: VITE_API_BASE_URL ?? '',
  logLevel: (VITE_API_LOG_LEVEL as any) ?? 'error',
});

/**
 * 创建独立的 API 客户端实例（用于需要不同配置的场景）。
 *
 * 示例:
 *   const adminClient = createApiClient({ baseURL: 'https://admin.api.com' });
 *   adminClient.setToken('admin-token');
 */
export function createApiClient(options?: ClientOptions): ApiClient {
  return new ApiClient(options);
}

// ─── 辅助类型导出 ─────────────────────────────────────────────────────────────

/** 从 ApiResponse 中提取数据类型 */
export type ExtractData<T> = T extends ApiResponse<infer D> ? D : T;

/** 从 PaginatedResponse 中提取项类型 */
export type ExtractItem<T> = T extends PaginatedResponse<infer I> ? I : T;
