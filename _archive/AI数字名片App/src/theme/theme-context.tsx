/**
 * Theme Context — 全局主题上下文
 * 提供 AppTheme 给所有子组件，支持 Dark / Light / System 三种模式
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { useColorScheme } from 'react-native';
import { DarkTheme, LightTheme, AppTheme, getPaperTheme } from './index';

export type ThemeMode = 'dark' | 'light' | 'system';

interface ThemeContextType {
  theme: AppTheme;
  paperTheme: ReturnType<typeof getPaperTheme>;
  colors: AppTheme['colors'];
  spacing: AppTheme['spacing'];
  radius: AppTheme['radius'];
  shadows: AppTheme['shadows'];
  typography: AppTheme['typography'];
  isDark: boolean;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | null>(null);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const systemColorScheme = useColorScheme();
  const [themeMode, setThemeMode] = useState<ThemeMode>('system');

  const isDark = useMemo(() => {
    if (themeMode === 'system') return systemColorScheme === 'dark';
    return themeMode === 'dark';
  }, [themeMode, systemColorScheme]);

  const theme = useMemo(() => (isDark ? DarkTheme : LightTheme), [isDark]);
  const paperTheme = useMemo(() => getPaperTheme(isDark), [isDark]);

  const toggleTheme = useCallback(() => {
    setThemeMode((prev) => {
      if (prev === 'system') {
        return systemColorScheme === 'dark' ? 'light' : 'dark';
      }
      return prev === 'dark' ? 'light' : 'dark';
    });
  }, [systemColorScheme]);

  const value = useMemo<ThemeContextType>(
    () => ({
      theme,
      paperTheme,
      colors: theme.colors,
      spacing: theme.spacing,
      radius: theme.radius,
      shadows: theme.shadows,
      typography: theme.typography,
      isDark,
      themeMode,
      setThemeMode,
      toggleTheme,
    }),
    [theme, paperTheme, isDark, themeMode, toggleTheme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export function useTheme(): ThemeContextType {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useTheme must be used within a <ThemeProvider>');
  }
  return ctx;
}

export default ThemeContext;
