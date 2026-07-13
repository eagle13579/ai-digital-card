/**
 * AI数字名片 — 设计 Token 系统 v2
 * 
 * 源自 taste-skill (42.8K⭐) 设计哲学
 * 融合 stripe-clone 商业化UI + impeccable (37.9K⭐) 设计一致性
 * 
 * 冷峻轻奢（Cold Luxury）— 深蓝黑 + 青绿
 */

export const colors = {
  primary: '#0F172A',
  primaryLight: '#1E293B',
  accent: '#2DD4BF',
  accentLight: '#5EEAD4',
  accentDark: '#14B8A6',
  surface: '#FFFFFF',
  surfaceAlt: '#F8FAFC',
  border: '#E2E8F0',
  borderLight: '#F1F5F9',
  text: '#0F172A',
  textSecondary: '#64748B',
  textTertiary: '#64748B',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  gradient: 'linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #2DD4BF 100%)',
  glassBg: 'rgba(255,255,255,0.7)',
  glassBorder: 'rgba(255,255,255,0.2)',
} as const;

export const spacing = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, '2xl': 48, '3xl': 64 } as const;
export const radius = { sm: 8, md: 12, lg: 16, xl: 24, full: '9999px' } as const;

export const shadows = {
  card: '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
  elevated: '0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)',
  modal: '0 20px 25px rgba(0,0,0,0.1), 0 8px 10px rgba(0,0,0,0.06)',
  glow: '0 0 20px rgba(45,212,191,0.15)',
} as const;

export const motion = {
  spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
  smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
  duration: { fast: 150, normal: 250, slow: 400 },
} as const;

export const glass = {
  background: 'rgba(255,255,255,0.7)',
  backdropFilter: 'blur(12px)',
  border: '1px solid rgba(255,255,255,0.2)',
  borderRadius: '16px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
} as const;

export const cardTemplates = [
  { id: 'default', name: '经典',    bg: '#0F172A', accent: '#2DD4BF', text: '#FFFFFF' },
  { id: 'ocean',   name: '深海',    bg: '#0C4A6E', accent: '#38BDF8', text: '#FFFFFF' },
  { id: 'rose',    name: '玫瑰金',  bg: '#1A0A0A', accent: '#F472B6', text: '#FFFFFF' },
  { id: 'green',   name: '翡翠',    bg: '#064E3B', accent: '#34D399', text: '#FFFFFF' },
  { id: 'purple',  name: '星云',    bg: '#1E1B4B', accent: '#A78BFA', text: '#FFFFFF' },
  { id: 'warm',    name: '暖阳',    bg: '#451A03', accent: '#FB923C', text: '#FFFFFF' },
  { id: 'slate',   name: '烟灰',    bg: '#1E293B', accent: '#94A3B8', text: '#FFFFFF' },
  { id: 'candy',   name: '糖果',    bg: '#1A0F14', accent: '#E879F9', text: '#FFFFFF' },
  { id: 'forest',  name: '森林',    bg: '#052E16', accent: '#4ADE80', text: '#FFFFFF' },
] as const;
