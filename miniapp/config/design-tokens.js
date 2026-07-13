/**
 * 设计Token常量
 * AI数智名片 - 微信小程序
 * 
 * 匹配 app.wxss 中的 CSS 自定义属性 (Design Tokens)
 * 供 JS 侧读取设计变量，无需硬编码颜色/间距/圆角等值
 * 
 * 参考: app.wxss 中的 --surface-*, --accent, --text-*, --space-* 等变量
 */

const DESIGN_TOKENS = {
  // === Surface 表面色 ===
  surface: {
    primary: '#0f0f1a',
    secondary: '#1a1a2e',
    tertiary: '#252540',
    glass: 'rgba(30, 30, 50, 0.6)',
    glassStrong: 'rgba(30, 30, 50, 0.95)',
  },

  // === Accent 主题色 ===
  accent: {
    primary: '#8b5cf6',
    light: '#a78bfa',
    dark: '#6d28d9',
    gradient: 'linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%)',
    gradientWarm: 'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%)',
    gradientCard: 'linear-gradient(135deg, rgba(139,92,246,0.12), rgba(6,182,212,0.08))',
    gradientHeader: 'linear-gradient(135deg, rgba(139,92,246,0.08), rgba(6,182,212,0.04))',
  },

  // === Text 文字色 ===
  text: {
    primary: '#ffffff',
    secondary: 'rgba(255, 255, 255, 0.72)',
    tertiary: 'rgba(255, 255, 255, 0.45)',
    disabled: 'rgba(255, 255, 255, 0.2)',
  },

  // === Border 边框色 ===
  border: {
    subtle: 'rgba(255, 255, 255, 0.06)',
    default: 'rgba(255, 255, 255, 0.1)',
    strong: 'rgba(255, 255, 255, 0.18)',
  },

  // === Semantic 语义色 ===
  semantic: {
    success: '#22c55e',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
  },

  // === Shadow 阴影 ===
  shadow: {
    sm: '0 2px 8px rgba(0, 0, 0, 0.2)',
    md: '0 4px 16px rgba(0, 0, 0, 0.25)',
    lg: '0 8px 32px rgba(0, 0, 0, 0.35)',
    glow: '0 0 20px rgba(139, 92, 246, 0.25)',
  },

  // === Typography 字体 ===
  font: {
    family: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"SF Pro Display"',
      '"PingFang SC"',
      '"Hiragino Sans GB"',
      '"Microsoft YaHei"',
      '"Helvetica Neue"',
      'sans-serif',
    ].join(', '),
    sizes: {
      xs: 11,
      sm: 13,
      base: 15,
      lg: 18,
      xl: 24,
      '2xl': 32,
    },
    weights: {
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },

  // === Spacing 间距 (4px 增量) ===
  space: {
    1: 4,
    2: 8,
    3: 12,
    4: 16,
    5: 20,
    6: 24,
    8: 32,
    10: 40,
    12: 48,
  },

  // === Radius 圆角 ===
  radius: {
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    full: 999,
  },

  // === Z-index ===
  z: {
    dropdown: 100,
    sticky: 200,
    overlay: 300,
    modal: 400,
    toast: 500,
  },
}

/**
 * 获取指定 token 的值，支持点号路径访问
 * @param {string} path - 点号分隔的路径，如 'accent.primary'、'space.4'
 * @param {*} fallback - 如果路径不存在返回的默认值
 * @returns {*}
 */
function getToken(path, fallback = undefined) {
  const keys = path.split('.')
  let current = DESIGN_TOKENS
  for (const key of keys) {
    if (current === null || typeof current !== 'object' || !(key in current)) {
      return fallback
    }
    current = current[key]
  }
  return current !== undefined ? current : fallback
}

module.exports = {
  DESIGN_TOKENS,
  getToken,
}
