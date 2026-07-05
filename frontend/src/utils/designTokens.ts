/**
 * designTokens — 辉光设计系统 Token 生成器
 * 
 * 基于MiniMax Token化设计系统(palette.py) + 产品类型自动推导
 * 可用在任何产品中统一管理品牌设计语言
 */

export type DocumentType = 
  | 'report' | 'proposal' | 'resume' | 'portfolio' 
  | 'landing' | 'dashboard' | 'social' | 'academic'
  | 'card' | 'invoice' | 'contract' | 'presentation';

export interface DesignTokens {
  colors: {
    primary: string;
    accent: string;
    accentLight: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    muted: string;
    border: string;
    success: string;
    warning: string;
    error: string;
  };
  typography: {
    fontDisplay: string;
    fontBody: string;
    fontMono: string;
    sizes: {
      h1: string;
      h2: string;
      h3: string;
      body: string;
      small: string;
      caption: string;
    };
    weights: {
      light: number;
      regular: number;
      medium: number;
      bold: number;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  radius: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
    full: string;
  };
  shadows: string[];
  animation: {
    duration: string;
    easing: string;
    stagger: string;
  };
  effects: {
    glassmorphism: string;
    glowColor: string;
    gradientPrimary: string;
    gradientAccent: string;
  };
}

const PALETTES: Record<DocumentType, Partial<DesignTokens['colors']>> = {
  report:     { primary: '#1B2A38', accent: '#3B6D8A', background: '#FAFAF8', text: '#2C2C30' },
  proposal:   { primary: '#22272E', accent: '#4E6070', background: '#FAFAF7', text: '#28282E' },
  resume:     { primary: '#FFFFFF', accent: '#1C3557', background: '#FFFFFF', text: '#222222' },
  portfolio:  { primary: '#191C20', accent: '#6A7A88', background: '#F8F8F8', text: '#28282E' },
  landing:    { primary: '#0F0F1A', accent: '#6C5CE7', background: '#FFFFFF', text: '#1A1A2E' },
  dashboard:  { primary: '#0F0F13', accent: '#6C5CE7', background: '#141418', text: '#E8E8EC' },
  social:     { primary: '#1A1A2E', accent: '#E94560', background: '#FFFFFF', text: '#16213E' },
  academic:   { primary: '#F5F4F0', accent: '#2A436A', background: '#FFFFFF', text: '#1A202C' },
  card:       { primary: '#1B2A38', accent: '#3B6D8A', background: '#FFFFFF', text: '#2C2C30' },
  invoice:    { primary: '#FFFFFF', accent: '#2D6B4F', background: '#FFFFFF', text: '#1A1A1A' },
  contract:   { primary: '#F8F7F4', accent: '#8B4513', background: '#FFFFFF', text: '#2C2C2C' },
  presentation: { primary: '#1A1A2E', accent: '#E94560', background: '#FFFFFF', text: '#16213E' },
};

export function generateTokens(type: DocumentType = 'landing'): DesignTokens {
  const palette = PALETTES[type] || PALETTES.landing;
  
  return {
    colors: {
      primary: palette.primary || '#0F0F1A',
      accent: palette.accent || '#6C5CE7',
      accentLight: adjustColor(palette.accent || '#6C5CE7', 40),
      background: palette.background || '#FFFFFF',
      surface: palette.background === '#FFFFFF' ? '#F8F8FA' : '#1A1A22',
      text: palette.text || '#1A1A2E',
      textSecondary: palette.text ? adjustColor(palette.text, 50) : '#6B7280',
      muted: '#9CA3AF',
      border: '#E5E7EB',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
    },
    typography: {
      fontDisplay: "'Inter', 'SF Pro Display', -apple-system, sans-serif",
      fontBody: "'Inter', 'SF Pro Text', -apple-system, sans-serif",
      fontMono: "'JetBrains Mono', 'Fira Code', monospace",
      sizes: { h1: '3.5rem', h2: '2.25rem', h3: '1.5rem', body: '1rem', small: '0.875rem', caption: '0.75rem' },
      weights: { light: 300, regular: 400, medium: 500, bold: 700 },
    },
    spacing: { xs: '0.25rem', sm: '0.5rem', md: '1rem', lg: '1.5rem', xl: '2rem', xxl: '4rem' },
    radius: { sm: '0.375rem', md: '0.5rem', lg: '0.75rem', xl: '1rem', full: '9999px' },
    shadows: [
      '0 1px 2px rgba(0,0,0,0.05)',
      '0 4px 6px rgba(0,0,0,0.07)',
      '0 10px 15px rgba(0,0,0,0.1)',
      '0 20px 25px rgba(0,0,0,0.15)',
      '0 25px 50px rgba(0,0,0,0.2)',
    ],
    animation: {
      duration: '300ms',
      easing: 'cubic-bezier(0.16, 1, 0.3, 1)',
      stagger: '50ms',
    },
    effects: {
      glassmorphism: 'backdrop-filter: blur(20px); background: rgba(255,255,255,0.05);',
      glowColor: palette.accent || '#6C5CE7',
      gradientPrimary: `linear-gradient(135deg, ${palette.primary || '#0F0F1A'}, ${adjustColor(palette.primary || '#0F0F1A', 20)})`,
      gradientAccent: `linear-gradient(135deg, ${palette.accent || '#6C5CE7'}, ${adjustColor(palette.accent || '#6C5CE7', -20)})`,
    },
  };
}

function adjustColor(hex: string, percent: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.min(255, Math.max(0, (num >> 16) + percent));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0xFF) + percent));
  const b = Math.min(255, Math.max(0, (num & 0xFF) + percent));
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
}

export default generateTokens;
