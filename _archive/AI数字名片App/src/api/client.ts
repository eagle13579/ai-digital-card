/**
 * AI数字名片 — Axios API 客户端
 * 功能:
 *  - baseURL 统一配置 (默认指向后端API服务)
 *  - JWT Token 自动注入 (Authorization header)
 *  - Token 过期自动刷新 (refresh token 机制)
 *  - 请求/响应拦截器 (日志, 错误统一处理)
 */

import axios, {
  AxiosInstance,
  AxiosError,
  InternalAxiosRequestConfig,
  AxiosResponse,
} from 'axios';
import * as SecureStore from 'expo-secure-store';

// ── Constants ───────────────────────────────────────────────────────────────

const STORAGE_KEYS = {
  ACCESS_TOKEN: 'ncard_access_token',
  REFRESH_TOKEN: 'ncard_refresh_token',
} as const;

// 可根据环境切换: 开发/测试/生产
const API_BASE_URL = __DEV__
  ? 'http://localhost:3000/api/v1'
  : 'https://api.ncard.ai/api/v1';

const TOKEN_REFRESH_ENDPOINT = '/auth/refresh';

// ── Token 管理 ──────────────────────────────────────────────────────────────

export const TokenManager = {
  async getAccessToken(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
    } catch {
      return null;
    }
  },

  async setAccessToken(token: string): Promise<void> {
    await SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN, token);
  },

  async getRefreshToken(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
    } catch {
      return null;
    }
  },

  async setTokens(access: string, refresh: string): Promise<void> {
    await Promise.all([
      SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN, access),
      SecureStore.setItemAsync(STORAGE_KEYS.REFRESH_TOKEN, refresh),
    ]);
  },

  async clearTokens(): Promise<void> {
    await Promise.all([
      SecureStore.deleteItemAsync(STORAGE_KEYS.ACCESS_TOKEN),
      SecureStore.deleteItemAsync(STORAGE_KEYS.REFRESH_TOKEN),
    ]);
  },

  async isAuthenticated(): Promise<boolean> {
    const token = await this.getAccessToken();
    return token !== null;
  },
};

// ── Axios 实例 ──────────────────────────────────────────────────────────────

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// ── 请求拦截器: 注入 JWT Token ──────────────────────────────────────────────

apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = await TokenManager.getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (__DEV__) {
      console.log(`[API] ➡ ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error),
);

// ── 响应拦截器: 统一错误处理 + Token 自动刷新 ────────────────────────────────

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null): void {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else if (token) {
      resolve(token);
    }
  });
  failedQueue = [];
}

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    if (__DEV__) {
      console.log(`[API] ⬅ ${response.status} ${response.config.url}`);
    }
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // 非 401 错误或已是重试请求，直接拒绝
    if (!error.response || error.response.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    // ── Token 自动刷新 ──
    if (isRefreshing) {
      // 已有刷新请求在进行中，将后续请求排队
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }
        return apiClient(originalRequest);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const refreshToken = await TokenManager.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await axios.post(`${API_BASE_URL}${TOKEN_REFRESH_ENDPOINT}`, {
        refreshToken,
      });

      const { accessToken, refreshToken: newRefreshToken } = response.data;
      await TokenManager.setTokens(accessToken, newRefreshToken);

      // 重放排队的请求
      processQueue(null, accessToken);

      // 重试原始请求
      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
      }
      return apiClient(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      // 刷新失败 -> 清除 Token -> 触发登出
      await TokenManager.clearTokens();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

// ── API 方法封装 ────────────────────────────────────────────────────────────

export const api = {
  get: <T = unknown>(url: string, params?: Record<string, unknown>) =>
    apiClient.get<T>(url, { params }).then((res) => res.data),

  post: <T = unknown>(url: string, data?: unknown) =>
    apiClient.post<T>(url, data).then((res) => res.data),

  put: <T = unknown>(url: string, data?: unknown) =>
    apiClient.put<T>(url, data).then((res) => res.data),

  patch: <T = unknown>(url: string, data?: unknown) =>
    apiClient.patch<T>(url, data).then((res) => res.data),

  delete: <T = unknown>(url: string) =>
    apiClient.delete<T>(url).then((res) => res.data),
};

// ── Auth API (独立于 apiClient, 无需 Token) ─────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    axios.post(`${API_BASE_URL}/auth/login`, { email, password }).then((res) => res.data),

  register: (data: { email: string; password: string; name: string }) =>
    axios.post(`${API_BASE_URL}/auth/register`, data).then((res) => res.data),

  logout: async () => {
    await TokenManager.clearTokens();
  },
};

// ── 移动端名片 API ───────────────────────────────────────────────────────────

export const cardApi = {
  /** 获取名片详情 */
  getDetail: (cardId: string) =>
    api.get<{
      id: string;
      name: string;
      title: string;
      company: string;
      email: string;
      phone: string;
      website: string;
      tags: string[];
      trustScore: number;
      contactCount: number;
      intimacy: string;
      todayVisits: number;
      monthUnlocks: number;
      totalShares: number;
      recentInteractions: Array<{ who: string; action: string; time: string }>;
    }>(`/mobile/card/${cardId}`),

  /** 更新名片信息 */
  update: (cardId: string, data: {
    name: string;
    title: string;
    company: string;
    email: string;
    phone: string;
    website: string;
    tags: string[];
  }) => api.put(`/mobile/card/${cardId}`, data),
};

// ── 移动端匹配 API ───────────────────────────────────────────────────────────

export const matchApi = {
  /** 获取匹配推荐列表 */
  getList: (params?: { search?: string; page?: number }) =>
    api.get<{
      items: Array<{
        id: string;
        name: string;
        title: string;
        trustScore: number;
        matchRate: number;
        tags: string[];
        mutualContacts?: number;
      }>;
      total: number;
    }>('/mobile/match', params),

  /** 获取匹配详情 */
  getDetail: (matchId: string) =>
    api.get<{
      id: string;
      name: string;
      title: string;
      company: string;
      tags: string[];
      bio: string;
      matchRate: number;
      trustScore: number;
      commonality: string;
      matchBreakdown: Array<{ label: string; score: number; color: string }>;
      mutualContacts: Array<{ id: string; name: string; title: string }>;
    }>(`/mobile/match/${matchId}`),
};

// ── 移动端 Feed/Dashboard API ──────────────────────────────────────────────

export const feedApi = {
  /** 获取首页动态流 */
  getFeed: () =>
    api.get<{
      greeting: string;
      todayVisits: number;
      trustScore: number;
      monthUnlocks: number;
      stats: Array<{ label: string; value: string; delta: string; color: string }>;
      recommendedAvatars: Array<{ id: string; name: string; desc: string; emoji: string }>;
      recentActivity: Array<{ who: string; action: string; time: string }>;
    }>('/mobile/feed'),
};

export default apiClient;
