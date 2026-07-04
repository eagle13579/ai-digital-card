/**
 * 本地图片占位符 — 适用于微信小程序环境
 * 替代 via.placeholder.com 等外部图片服务（小程序无法加载外域图片）
 * 使用 SVG data URI，无需额外资源文件
 */

// 生成纯色 SVG data URI
function svgPlaceholder(width: number, height: number, bgColor = '#e8e8e8', text = ''): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
    <rect fill="${bgColor}" width="${width}" height="${height}"/>
    ${text ? `<text fill="#999" font-size="${Math.min(width, height) * 0.15}" x="50%" y="50%" text-anchor="middle" dominant-baseline="central">${text}</text>` : ''}
  </svg>`
  return 'data:image/svg+xml,' + encodeURIComponent(svg)
}

// 预定义的常用占位符
export const PLACEHOLDER = {
  avatar80:  svgPlaceholder(80, 80, '#e8e8e8', '?'),
  avatar64:  svgPlaceholder(64, 64, '#e8e8e8', '?'),
  avatar120: svgPlaceholder(120, 120, '#e8e8e8', '?'),
  cover280x200: svgPlaceholder(280, 200, '#e8e8e8', '暂无图片'),
  cover280x180: svgPlaceholder(280, 180, '#e8e8e8', '暂无图片'),
  cover280x160: svgPlaceholder(280, 160, '#e8e8e8', '暂无图片'),
  // 通用 fallback
  default: svgPlaceholder(100, 100, '#e8e8e8', ''),
}
