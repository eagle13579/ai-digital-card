import Taro from '@tarojs/taro'

/**
 * 分享裂变工具函数
 * 记录每日分享次数，达到上限后不再累计
 */

/** 获取今日分享次数 key（格式：share_count_YYYYMMDD） */
function getTodayKey(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `share_count_${y}${m}${d}`
}

/** 每日分享次数上限 */
export const MAX_SHARE_PER_DAY = 3

/** 获取今日已分享次数 */
export function getTodayShareCount(): number {
  try {
    const key = getTodayKey()
    const count = Taro.getStorageSync(key)
    return typeof count === 'number' ? count : 0
  } catch {
    return 0
  }
}

/** 获取今日剩余可分享次数（用于增加额外AI调用次数） */
export function getRemainingShareCount(): number {
  const used = getTodayShareCount()
  return Math.max(0, MAX_SHARE_PER_DAY - used)
}

/** 分享次数+1，返回增加后的次数；超过上限不再增加，返回-1 */
export function incrementShareCount(): number {
  const current = getTodayShareCount()
  if (current >= MAX_SHARE_PER_DAY) {
    return -1 // 已达上限
  }
  const key = getTodayKey()
  const newCount = current + 1
  Taro.setStorageSync(key, newCount)
  return newCount
}

/** 获取分享次数描述文本 */
export function getShareLimitText(): string {
  const remaining = getRemainingShareCount()
  if (remaining <= 0) {
    return '今日分享次数已用完'
  }
  return `分享得额外AI调用次数（今日剩余 ${remaining} 次）`
}
