import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { api } from '../api/client';

// ─── 类型定义 ─────────────────────────────────────────────────────────────────

export interface User {
  id: number;
  name: string;
  phone: string;
  email?: string;
  avatar?: string;
  role?: string;
}

export interface AuthState {
  /** JWT token */
  token: string | null;
  /** 当前用户信息 */
  user: User | null;
  /** 是否已认证 */
  isAuthenticated: boolean;
  /** 是否正在加载（检查 token 有效性） */
  loading: boolean;
  /** 登录 */
  login: (phone: string, password: string) => Promise<void>;
  /** 登出 */
  logout: () => void;
  /** 更新用户信息 */
  updateUser: (user: User) => void;
}

// ─── Context ─────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthState | undefined>(undefined);

// ─── Provider ────────────────────────────────────────────────────────────────

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setToken] = useState<string | null>(() => api.loadToken());
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const isAuthenticated = !!token;

  // 初始化时尝试获取用户信息
  useEffect(() => {
    if (token) {
      api.get<User>('/api/auth/me')
        .then(res => {
          if (res.code === 200 && res.data) {
            setUser(res.data);
          } else {
            // token 无效，清除
            api.removeToken();
            setToken(null);
          }
        })
        .catch(() => {
          api.removeToken();
          setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async (phone: string, password: string) => {
    const res = await api.post<{ token: string; user: User }>('/api/auth/login', { phone, password });
    if (res.code === 200 && res.data) {
      api.saveToken(res.data.token);
      setToken(res.data.token);
      setUser(res.data.user);
    } else {
      throw new Error(res.message || '登录失败');
    }
  }, []);

  const logout = useCallback(() => {
    api.removeToken();
    setToken(null);
    setUser(null);
  }, []);

  const updateUser = useCallback((newUser: User) => {
    setUser(newUser);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated, loading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default useAuth;
