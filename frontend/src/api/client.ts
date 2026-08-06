const API_BASE = ''; // 通过Nginx代理到后端

export interface ApiResponse<T> {
  code: number;
  message: string;
  data?: T;
}

function loadToken(): string | null { return localStorage.getItem('token'); }
function saveToken(t: string) { localStorage.setItem('token', t); }
function removeToken() { localStorage.removeItem('token'); }

// ── CSRF 支持（Double Submit Cookie）─────────────────────────────
// 后端 CSRF 中间件要求 POST/PUT/DELETE 带 X-CSRF-Token 头（与 cookie 值一致）
// 首次调用时 GET /api/csrf/token 种下 cookie，之后从 document.cookie 读取
let csrfPromise: Promise<string> | null = null;

function readCsrfFromCookie(): string | null {
  if (typeof document === 'undefined') return null;
  const m = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}

async function ensureCsrfToken(): Promise<string> {
  const existing = readCsrfFromCookie();
  if (existing) return existing;
  if (!csrfPromise) {
    csrfPromise = (async () => {
      try {
        await fetch(API_BASE + '/api/csrf/token', { credentials: 'same-origin' });
      } catch { /* 忽略，后面再尝试 */ }
      return readCsrfFromCookie() || '';
    })().finally(() => { csrfPromise = null; });
  }
  return csrfPromise;
}

async function request<T>(path: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const t = loadToken();
  const isFormData = options?.body instanceof FormData;
  const method = (options?.method || 'GET').toUpperCase();
  const headers: Record<string,string> = isFormData ? {} : {'Content-Type': 'application/json'};
  if (t) headers['Authorization'] = 'Bearer ' + t;
  // 非 GET 请求带 CSRF token（FormData 也带，中间件从 body 读不到就靠 header）
  if (method !== 'GET' && !isFormData) {
    const csrf = await ensureCsrfToken();
    if (csrf) headers['X-CSRF-Token'] = csrf;
  }
  try {
    const res = await fetch(API_BASE + path, {...options, headers, credentials: 'same-origin'});
    if (!res.ok) {
      return { code: res.status, message: `HTTP ${res.status}: ${res.statusText}` };
    }
    const json = await res.json();
    if (json.code !== undefined) return json;
    return { code: 200, message: 'ok', data: json };
  } catch (e: any) {
    console.error('[API Error]', path, e);
    return { code: 500, message: e.message || '网络错误，请检查连接' };
  }
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: any) => request<T>(path, {method:'POST', body: JSON.stringify(body)}),
  put: <T>(path: string, body: any) => request<T>(path, {method:'PUT', body: JSON.stringify(body)}),
  delete: <T>(path: string) => request<T>(path, {method:'DELETE'}),
  request: <T>(path: string, options?: RequestInit) => request<T>(path, options),
  saveToken, loadToken, removeToken,
};
