import AsyncStorage from '@react-native-async-storage/async-storage';

// ---------------------------------------------------------------------------
// Storage keys
// ---------------------------------------------------------------------------
const KEYS = {
  AUTH_TOKEN: '@ai_card/auth_token',
  USER_PROFILE: '@ai_card/user_profile',
  SETTINGS: '@ai_card/settings',
} as const;

// ---------------------------------------------------------------------------
// Generic helpers
// ---------------------------------------------------------------------------
async function getItem<T = string>(key: string): Promise<T | null> {
  try {
    const raw = await AsyncStorage.getItem(key);
    if (raw === null) return null;
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

async function setItem(key: string, value: unknown): Promise<void> {
  await AsyncStorage.setItem(key, JSON.stringify(value));
}

async function removeItem(key: string): Promise<void> {
  await AsyncStorage.removeItem(key);
}

async function clearAll(): Promise<void> {
  await AsyncStorage.multiRemove(Object.values(KEYS));
}

// ---------------------------------------------------------------------------
// Domain-specific helpers
// ---------------------------------------------------------------------------
export async function getAuthToken(): Promise<string | null> {
  return AsyncStorage.getItem(KEYS.AUTH_TOKEN);
}

export async function setAuthToken(token: string): Promise<void> {
  await AsyncStorage.setItem(KEYS.AUTH_TOKEN, token);
}

export async function removeAuthToken(): Promise<void> {
  await AsyncStorage.removeItem(KEYS.AUTH_TOKEN);
}

export async function getUserProfile<T = Record<string, unknown>>(): Promise<T | null> {
  return getItem<T>(KEYS.USER_PROFILE);
}

export async function setUserProfile(profile: unknown): Promise<void> {
  await setItem(KEYS.USER_PROFILE, profile);
}

export async function getSettings<T = Record<string, unknown>>(): Promise<T | null> {
  return getItem<T>(KEYS.SETTINGS);
}

export async function setSettings(settings: unknown): Promise<void> {
  await setItem(KEYS.SETTINGS, settings);
}

export { KEYS, clearAll };
