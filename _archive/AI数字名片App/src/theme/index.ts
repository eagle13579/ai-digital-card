/**
 * AI数字名片 — Mobile Design Token 主题
 * 基于 Glass Tech Design Tokens (glass-tokens.ts) 提取的移动端主题系统
 * 支持 Dark / Light 双模式，与 admin-web glass-tech.css v3.1 保持一致
 */

import { MD3DarkTheme, MD3LightTheme, configureFonts } from 'react-native-paper';

// ── Typography ──────────────────────────────────────────────────────────────
export const typography = {
  fontFamily: {
    regular: undefined as string | undefined,  // system default
    medium: undefined as string | undefined,
    bold: undefined as string | undefined,
    mono: 'monospace' as string | undefined,
  },
  fontSize: {
    xs: 10,
    sm: 12,
    md: 14,
    lg: 17,
    xl: 20,
    xxl: 26,
    xxxl: 32,
  },
  fontWeight: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
    extrabold: '800' as const,
  },
  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.75,
  },
};

// ── Spacing ─────────────────────────────────────────────────────────────────
export const spacing = {
  xxs: 2,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
  xxxxl: 48,
};

// ── Border Radius ────────────────────────────────────────────────────────────
export const radius = {
  sm: 6,
  md: 10,
  lg: 16,
  xl: 24,
  full: 9999,
};

// ── Shadows (iOS) ────────────────────────────────────────────────────────────
export const shadows = {
  sm: {
    shadowColor: '#000',
    shadowOpacity: 0.4,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOpacity: 0.5,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
  lg: {
    shadowColor: '#000',
    shadowOpacity: 0.6,
    shadowRadius: 32,
    shadowOffset: { width: 0, height: 12 },
    elevation: 16,
  },
};

// ── Dark Theme ──────────────────────────────────────────────────────────────
const darkColors = {
  // Brand
  primary: '#6366f1',
  primaryGlow: 'rgba(99, 102, 241, 0.25)',
  primaryLight: '#818cf8',
  primaryDark: '#4f46e5',

  // Semantic
  success: '#22c55e',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',

  // Text
  textPrimary: 'rgba(255, 255, 255, 0.95)',
  textSecondary: 'rgba(255, 255, 255, 0.65)',
  textTertiary: 'rgba(255, 255, 255, 0.40)',
  textInverse: 'rgba(0, 0, 0, 0.85)',

  // Surfaces
  background: '#0a0a0f',
  backgroundDarker: '#06060a',
  surface: 'rgba(255, 255, 255, 0.04)',
  surfaceElevated: 'rgba(255, 255, 255, 0.08)',

  // Glass
  glassBg: 'rgba(255, 255, 255, 0.06)',
  glassBgStrong: 'rgba(255, 255, 255, 0.10)',
  glassBgHover: 'rgba(255, 255, 255, 0.12)',
  glassBorder: 'rgba(255, 255, 255, 0.10)',
  glassBorderStrong: 'rgba(255, 255, 255, 0.18)',
  glassShadow: 'rgba(0, 0, 0, 0.40)',

  // Tab bar
  tabBarBg: 'rgba(10, 10, 15, 0.85)',
  tabBarBorder: 'rgba(255, 255, 255, 0.10)',
};

// ── Light Theme ───────────────────────────────────────────────────────────────
const lightColors: typeof darkColors = {
  primary: '#4f46e5',
  primaryGlow: 'rgba(79, 70, 229, 0.18)',
  primaryLight: '#6366f1',
  primaryDark: '#4338ca',

  success: '#22c55e',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',

  textPrimary: 'rgba(15, 23, 42, 0.92)',
  textSecondary: 'rgba(15, 23, 42, 0.65)',
  textTertiary: 'rgba(15, 23, 42, 0.45)',
  textInverse: 'rgba(255, 255, 255, 0.95)',

  background: '#f6f7fb',
  backgroundDarker: '#eef1f7',
  surface: '#ffffff',
  surfaceElevated: '#ffffff',

  glassBg: 'rgba(255, 255, 255, 0.75)',
  glassBgStrong: 'rgba(255, 255, 255, 0.92)',
  glassBgHover: 'rgba(255, 255, 255, 0.98)',
  glassBorder: 'rgba(15, 23, 42, 0.08)',
  glassBorderStrong: 'rgba(15, 23, 42, 0.16)',
  glassShadow: 'rgba(15, 23, 42, 0.12)',

  tabBarBg: 'rgba(246, 247, 251, 0.92)',
  tabBarBorder: 'rgba(15, 23, 42, 0.08)',
};

// ── Theme Bundle ────────────────────────────────────────────────────────────
export interface AppTheme {
  dark: boolean;
  colors: typeof darkColors;
  typography: typeof typography;
  spacing: typeof spacing;
  radius: typeof radius;
  shadows: typeof shadows;
}

export const DarkTheme: AppTheme = {
  dark: true,
  colors: darkColors,
  typography,
  spacing,
  radius,
  shadows,
};

export const LightTheme: AppTheme = {
  dark: false,
  colors: lightColors,
  typography,
  spacing,
  radius,
  shadows,
};

// ── React Native Paper 主题适配 ──────────────────────────────────────────────
const paperFontConfig = { fontFamily: 'System' };

export const PaperDarkTheme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    primary: darkColors.primary,
    primaryContainer: darkColors.primaryGlow,
    secondary: darkColors.primaryLight,
    background: darkColors.background,
    surface: darkColors.glassBgStrong,
    surfaceVariant: darkColors.glassBg,
    error: darkColors.danger,
    onPrimary: '#ffffff',
    onBackground: darkColors.textPrimary,
    onSurface: darkColors.textPrimary,
    onSurfaceVariant: darkColors.textSecondary,
    outline: darkColors.glassBorder,
    outlineVariant: darkColors.glassBorderStrong,
  },
  fonts: configureFonts({ config: paperFontConfig }),
};

export const PaperLightTheme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: lightColors.primary,
    primaryContainer: lightColors.primaryGlow,
    secondary: lightColors.primaryLight,
    background: lightColors.background,
    surface: lightColors.glassBgStrong,
    surfaceVariant: lightColors.glassBg,
    error: lightColors.danger,
    onPrimary: '#ffffff',
    onBackground: lightColors.textPrimary,
    onSurface: lightColors.textPrimary,
    onSurfaceVariant: lightColors.textSecondary,
    outline: lightColors.glassBorder,
    outlineVariant: lightColors.glassBorderStrong,
  },
  fonts: configureFonts({ config: paperFontConfig }),
};

// ── Helper: 获取当前主题 ─────────────────────────────────────────────────────
export function getTheme(isDark: boolean): AppTheme {
  return isDark ? DarkTheme : LightTheme;
}

export function getPaperTheme(isDark: boolean) {
  return isDark ? PaperDarkTheme : PaperLightTheme;
}

export default DarkTheme;
