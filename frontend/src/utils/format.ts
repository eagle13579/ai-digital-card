/**
 * AI数字名片 — 通用时间格式化工具
 */

/**
 * 相对时间格式化（用于分析页、访客列表等）
 * 输出如「刚刚」「3分钟前」「2小时前」「5天前」
 */
export function formatRelativeTime(
  iso: string | null,
  t: (key: string, vars?: Record<string, string | number>) => string,
): string {
  if (!iso) return '';
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return t('analytics.time.justNow');
  if (mins < 60) return t('analytics.time.minutesAgo', { n: mins });
  const hours = Math.floor(mins / 60);
  if (hours < 24) return t('analytics.time.hoursAgo', { n: hours });
  const days = Math.floor(hours / 24);
  if (days < 7) return t('analytics.time.daysAgo', { n: days });
  return d.toLocaleDateString('zh-CN');
}

/**
 * 简单时间格式化（用于实验列表等）
 * 输出如「2024/1/15 14:30:00」
 */
export function formatDateTime(iso: string | null): string {
  if (!iso) return '-';
  const d = new Date(iso);
  return d.toLocaleString('zh-CN');
}
