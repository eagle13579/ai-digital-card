/**
 * 会员等级体系 — 全站统一
 * 
 * 标准化三档：
 *   free       → Free
 *   pro        → Pro
 *   enterprise → Enterprise
 * 
 * 别名兼容（旧数据映射到三档）：
 *   gold    → Pro
 *   silver  → Pro
 *   diamond → Enterprise
 *   board   → Enterprise
 */

const LEVEL_MAP = {
  free: 'Free',
  pro: 'Pro',
  enterprise: 'Enterprise',
  // 别名兼容
  gold: 'Pro',
  silver: 'Pro',
  diamond: 'Enterprise',
  board: 'Enterprise',
}

/** 根据等级ID获取显示文本 */
function getLevelText(levelId) {
  return LEVEL_MAP[levelId] || 'Free'
}

/** 获取等级对应的CSS class名 */
function getLevelClass(levelId) {
  const map = { free: 'free', pro: 'pro', enterprise: 'enterprise', gold: 'pro', silver: 'pro', diamond: 'enterprise', board: 'enterprise' }
  return map[levelId] || 'free'
}

module.exports = { LEVEL_MAP, getLevelText, getLevelClass }
