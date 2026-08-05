# F06 — API 统一响应格式

## 心智模型（Mental Model）

所有 API 响应遵循统一的 **{ code, message, data }** 三字段格式。前端 Axios 拦截器自动解包 `res.data`，使业务代码只关心 `data` 字段。

```
后端响应结构：
{
  code: 0,           // 业务码: 0=成功, 非0=失败
  message: 'xxx',    // 人类可读消息
  data: { ... }      // 实际数据（成功时）或 null（失败时）
}

前端接收：
api.get('/xxx') → 拦截器解包 → 直接拿到 data 部分
```

## Architecture Decision Records

### ADR-014: 统一 code+message+data 响应格式

| 项目 | 决策 |
|------|------|
| 决策 | 所有 API 响应使用 `{ code: number, message: string, data: any }` |
| 替代方案 | 直接返回数据/裸 status code |
| 理由 | 1) 前端可通过 code 统一判断成败；2) message 直接用于 Toast/提示；3) 标准化后方便 mock 和文档生成 |
| 后果 | 每个路由需包裹响应结构，增加少量样板代码 |

### ADR-015: Axios 响应拦截器自动解包 `res.data`

| 项目 | 决策 |
|------|------|
| 上下文 | 前端希望业务代码中 `api.get()` 直接返回 `data` 字段，而非完整 response |
| 决策 | 拦截器 `response.use(res => res.data)` 自动解包 |
| 理由 | 每个组件调用 API 时不用重复写 `.data`；错误统一抛出 |
| 后果 | 调试时需注意拦截器已剥去外层；网络层错误仍需单独处理 |

### ADR-016: 401 自动清除 Token 并跳转登录

| 项目 | 决策 |
|------|------|
| 上下文 | Token 过期或无效时需引导用户重新登录 |
| 决策 | 响应拦截器捕获 401，清除 localStorage 中的 token，跳转 #/login |
| 理由 | 集中处理认证失效，每个接口无需单独做 401 判断 |
| 后果 | 静默清除可能导致用户疑惑（无弹窗提示） |

## 核心代码提取

### 后端响应模式（所有路由统一）

```typescript
// 成功
res.json({ code: 0, data: result });
res.json({ code: 0, message: '操作成功', data: result });

// 参数错误
res.status(400).json({ code: 400, message: '手机号格式不正确' });

// 业务错误
res.status(400).json({ code: 400, message: '已经是平台成员' });

// 未找到
res.status(404).json({ code: 404, message: '平台不存在' });

// 服务器错误
res.status(500).json({ code: 500, message: '服务器错误' });
```

### 前端 Axios 拦截器

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// 请求拦截器 - 注入 Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - 统一解包 + 401处理
api.interceptors.response.use(
  (res) => res.data,       // 自动解包：api.get() 直接得到 data
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.hash = '#/login';
    }
    return Promise.reject(err.response?.data || { message: '网络错误' });
  }
);

export default api;
```

### 前端 API 模块示例

```typescript
export const authAPI = {
  login: (phone: string) => api.post('/auth/login', { phone, agreeTerms: true }),
  sendSms: (phone: string) => api.post('/auth/sms/send', { phone }),
  getMe: () => api.get('/auth/me'),
};

export const connectionAPI = {
  request: (targetUserId: string, message?: string) =>
    api.post('/connections/request', { targetUserId, message }),
  findPath: (targetUserId: string) => api.get(`/connections/path/${targetUserId}`),
};
```

## 业务码规范

| code | 含义 |
|------|------|
| 0 | 成功 |
| 400 | 参数错误 / 业务规则不满足 |
| 401 | 未认证 / Token 过期 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## Zustand 状态管理示意

```typescript
import { create } from 'zustand';

interface AppState {
  token: string | null;
  userId: string | null;
  userInfo: any | null;
  isLoggedIn: boolean;

  setAuth: (token: string, userId: string) => void;
  setUserInfo: (info: any) => void;
  logout: () => void;
}

export const useStore = create<AppState>((set) => ({
  token: localStorage.getItem('token'),
  userId: localStorage.getItem('userId'),
  userInfo: null,
  isLoggedIn: !!localStorage.getItem('token'),

  setAuth: (token, userId) => {
    localStorage.setItem('token', token);
    localStorage.setItem('userId', userId);
    set({ token, userId, isLoggedIn: true });
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    set({ token: null, userId: null, userInfo: null, isLoggedIn: false });
  },
}));
```

## 吸收建议

| 询赋实现 | AI数智名片适配方案 |
|----------|-------------------|
| Axios | 微信小程序使用 wx.request 封装类似拦截器 |
| localStorage | 使用 wx.setStorageSync / wx.getStorageSync |
| Zustand | 小程序使用 mobx-miniprogram 或全局 app 状态 |
| hash路由跳转 | 使用 wx.navigateTo / wx.switchTab |
| 统一响应格式 {code, message, data} | **强烈建议保留** |

## 可复用程度

- **响应格式设计**: 100% 可复用
- **Axios 拦截器模式**: 70% 需适配微信小程序 API
- **Zustand 状态管理**: 60% 需替换为小程序状态管理方案
