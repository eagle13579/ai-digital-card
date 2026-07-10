import { useState, useEffect, useCallback } from 'react';
import { getAuthToken, setAuthToken, removeAuthToken, getUserProfile, setUserProfile, clearAll } from '../utils/storage';
import { apiPost } from '../api/client';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  phone?: string;
  company?: string;
  title?: string;
}

export interface AuthState {
  /** Whether the token has been loaded from storage (hydrated) */
  isHydrated: boolean;
  /** Authenticated user profile (null when not logged in) */
  user: UserProfile | null;
  /** Raw JWT token string */
  token: string | null;
  /** True while an auth request is in-flight */
  isLoading: boolean;
  /** Most recent error message */
  error: string | null;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------
export function useAuth() {
  const [state, setState] = useState<AuthState>({
    isHydrated: false,
    user: null,
    token: null,
    isLoading: false,
    error: null,
  });

  // ---- Hydrate from storage on mount ----
  useEffect(() => {
    (async () => {
      try {
        const [token, profile] = await Promise.all([
          getAuthToken(),
          getUserProfile<UserProfile>(),
        ]);
        setState((prev) => ({
          ...prev,
          isHydrated: true,
          user: profile,
          token,
        }));
      } catch {
        setState((prev) => ({ ...prev, isHydrated: true }));
      }
    })();
  }, []);

  // ---- Login ----
  const login = useCallback(async (email: string, password: string) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const res = await apiPost<{ access_token: string; user: UserProfile }>(
        '/api/v1/auth/login',
        { email, password },
      );
      const { access_token, user } = res;

      // Persist
      await Promise.all([
        setAuthToken(access_token),
        setUserProfile(user),
      ]);

      setState((prev) => ({
        ...prev,
        isLoading: false,
        token: access_token,
        user,
        error: null,
      }));

      return user;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setState((prev) => ({ ...prev, isLoading: false, error: message }));
      throw err;
    }
  }, []);

  // ---- Logout ----
  const logout = useCallback(async () => {
    await clearAll();
    setState({
      isHydrated: true,
      user: null,
      token: null,
      isLoading: false,
      error: null,
    });
  }, []);

  return { ...state, login, logout };
}
