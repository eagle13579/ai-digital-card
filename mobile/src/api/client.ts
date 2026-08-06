import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// ---------------------------------------------------------------------------
// Environment / configuration
// ---------------------------------------------------------------------------
const DEV_BASE_URL = 'http://localhost:8002';
const PROD_BASE_URL = 'https://api.liankebao.top';

const BASE_URL = __DEV__ ? DEV_BASE_URL : PROD_BASE_URL;

// ---------------------------------------------------------------------------
// Singleton axios instance
// ---------------------------------------------------------------------------
const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ---------------------------------------------------------------------------
// Request interceptor – attach auth token if available
// ---------------------------------------------------------------------------
client.interceptors.request.use(
  (config) => {
    // Token will be injected by the caller or from storage
    const token = config._authToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ---------------------------------------------------------------------------
// Response interceptor – normalise errors
// ---------------------------------------------------------------------------
client.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      const message = data?.detail ?? data?.message ?? `Request failed (${status})`;
      return Promise.reject(new Error(message));
    }
    if (error.request) {
      return Promise.reject(new Error('Network error – please check your connection'));
    }
    return Promise.reject(error);
  },
);

// ---------------------------------------------------------------------------
// Typed helpers (optional convenience wrappers)
// ---------------------------------------------------------------------------
export async function apiGet<T = unknown>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<T> {
  const res = await client.get<T>(url, config);
  return res.data;
}

export async function apiPost<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const res = await client.post<T>(url, data, config);
  return res.data;
}

export async function apiPut<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const res = await client.put<T>(url, data, config);
  return res.data;
}

export async function apiDelete<T = unknown>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<T> {
  const res = await client.delete<T>(url, config);
  return res.data;
}

export default client;
