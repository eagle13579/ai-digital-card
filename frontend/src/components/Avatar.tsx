import { User } from 'lucide-react';
import clsx from 'clsx';

// ============================================================
// 头像组件
// 支持: 图片 / 首字母 / 默认图标
// 尺寸: sm / md / lg / xl
// 形状: 圆形（默认）/ 圆角方形
// ============================================================

type AvatarSize = 'sm' | 'md' | 'lg' | 'xl';

interface AvatarProps {
  /** 头像图片 URL（可选） */
  src?: string;
  /** 替代文本 */
  alt?: string;
  /** 用户姓名（用于生成首字母兜底） */
  name?: string;
  /** 尺寸 */
  size?: AvatarSize;
  /** 形状 — circle（默认）| rounded（圆角方形） */
  shape?: 'circle' | 'rounded';
  /** 在线状态指示器 */
  status?: 'online' | 'offline' | 'away';
  /** 自定义类名 */
  className?: string;
}

const sizeMap: Record<AvatarSize, string> = {
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-14 h-14 text-base',
  xl: 'w-20 h-20 text-xl',
};

const statusDotMap: Record<AvatarSize, string> = {
  sm: 'w-2 h-2 right-0 bottom-0',
  md: 'w-2.5 h-2.5 right-0 bottom-0',
  lg: 'w-3 h-3 right-0.5 bottom-0.5',
  xl: 'w-3.5 h-3.5 right-0.5 bottom-0.5',
};

const statusColorMap: Record<string, string> = {
  online: 'bg-emerald-500',
  offline: 'bg-slate-400',
  away: 'bg-amber-400',
};

/**
 * 获取姓名首字母（最多2个字符）
 */
function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

/**
 * 根据姓名生成固定背景色
 */
function getColorFromName(name: string): string {
  const colors = [
    'bg-sky-500', 'bg-purple-500', 'bg-emerald-500',
    'bg-amber-500', 'bg-rose-500', 'bg-indigo-500',
    'bg-teal-500', 'bg-pink-500', 'bg-cyan-500', 'bg-orange-500',
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

/**
 * Avatar — 用户头像组件
 *
 * 优先展示图片；无图片但有姓名时展示首字母色块；兜底展示 User 图标。
 * 支持在线/离线/离开状态指示器。
 */
export default function Avatar({
  src,
  alt = '',
  name,
  size = 'md',
  shape = 'circle',
  status,
  className,
}: AvatarProps) {
  const shapeClass = shape === 'circle' ? 'rounded-full' : 'rounded-xl';
  const dotPosition = shape === 'circle'
    ? statusDotMap[size]
    : statusDotMap[size]?.replace('right-0', 'right-0.5').replace('bottom-0', 'bottom-0.5');

  return (
    <div className={clsx('relative inline-flex shrink-0', className)}>
      {/* Image */}
      {src ? (
        <img
          src={src}
          alt={alt || name || 'avatar'}
          className={clsx(
            'object-cover',
            sizeMap[size],
            shapeClass,
            'ring-2 ring-white',
          )}
        />
      ) : name ? (
        /* Initials fallback */
        <div
          className={clsx(
            'flex items-center justify-center font-bold text-white',
            sizeMap[size],
            shapeClass,
            getColorFromName(name),
          )}
          aria-label={name}
        >
          {getInitials(name)}
        </div>
      ) : (
        /* Default fallback */
        <div
          className={clsx(
            'flex items-center justify-center bg-slate-200 text-slate-400',
            sizeMap[size],
            shapeClass,
          )}
        >
          <User className={size === 'sm' ? 'w-4 h-4' : size === 'md' ? 'w-5 h-5' : size === 'lg' ? 'w-7 h-7' : 'w-10 h-10'} />
        </div>
      )}

      {/* Status indicator */}
      {status && (
        <span
          className={clsx(
            'absolute block rounded-full ring-2 ring-white',
            dotPosition,
            statusColorMap[status],
          )}
          aria-label={status}
        />
      )}
    </div>
  );
}
