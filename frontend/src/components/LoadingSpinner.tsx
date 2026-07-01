import { Loader2 } from 'lucide-react';
import clsx from 'clsx';

// ============================================================
// 加载旋转器组件
// 尺寸: sm / md / lg
// 模式: 内联（默认）/ 全页覆盖
// ============================================================

type SpinnerSize = 'sm' | 'md' | 'lg';

interface LoadingSpinnerProps {
  /** 尺寸 */
  size?: SpinnerSize;
  /** 全页模式 — 居中覆盖整个父容器 */
  fullPage?: boolean;
  /** 自定义提示文字（显示在旋转器下方） */
  label?: string;
  /** 自定义类名 */
  className?: string;
}

const sizeMap: Record<SpinnerSize, string> = {
  sm: 'w-4 h-4',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
};

const labelSizeMap: Record<SpinnerSize, string> = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
};

/**
 * LoadingSpinner — 加载旋转器组件
 *
 * 支持 sm / md / lg 三种尺寸，可独立使用或作为全页覆盖层。
 */
export default function LoadingSpinner({
  size = 'md',
  fullPage = false,
  label,
  className,
}: LoadingSpinnerProps) {
  const spinner = (
    <div
      className={clsx(
        'flex flex-col items-center justify-center gap-3',
        fullPage && 'min-h-[200px]',
        className,
      )}
      role="status"
      aria-label={label || '加载中'}
    >
      <Loader2
        className={clsx(
          'animate-spin text-primary',
          sizeMap[size],
        )}
        aria-hidden="true"
      />
      {label && (
        <span className={clsx(
          'text-text-muted',
          labelSizeMap[size],
        )}>
          {label}
        </span>
      )}
    </div>
  );

  if (fullPage) {
    return (
      <div className="fixed inset-0 z-50 bg-white/60 backdrop-blur-sm flex items-center justify-center">
        {spinner}
      </div>
    );
  }

  return spinner;
}
