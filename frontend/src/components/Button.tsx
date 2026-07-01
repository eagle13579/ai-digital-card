import { ButtonHTMLAttributes, ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import clsx from 'clsx';

// ============================================================
// 通用按钮组件
// 变体: primary | secondary | outline
// 状态: loading | disabled
// ============================================================

type ButtonVariant = 'primary' | 'secondary' | 'outline';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** 按钮变体 */
  variant?: ButtonVariant;
  /** 加载中状态 — 显示旋转图标并禁用交互 */
  loading?: boolean;
  /** 图标（前置） */
  icon?: ReactNode;
  /** 图标（后置） */
  iconRight?: ReactNode;
  /** 全宽模式 */
  fullWidth?: boolean;
  /** 子元素 */
  children?: ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-primary text-white hover:bg-primary/90 active:bg-primary/80 focus-visible:ring-primary/40',
  secondary:
    'bg-slate-100 text-on-surface hover:bg-slate-200 active:bg-slate-300 focus-visible:ring-slate-300/40',
  outline:
    'border border-border-light text-on-surface bg-transparent hover:bg-slate-50 active:bg-slate-100 focus-visible:ring-border-light/40',
};

export default function Button({
  variant = 'primary',
  loading = false,
  disabled = false,
  icon,
  iconRight,
  fullWidth = false,
  children,
  className,
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <button
      disabled={isDisabled}
      className={clsx(
        // Base
        'inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium',
        'transition-all duration-200 select-none',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1',
        // Variant
        variantStyles[variant],
        // States
        isDisabled && 'opacity-50 cursor-not-allowed pointer-events-none',
        !isDisabled && 'cursor-pointer',
        // Width
        fullWidth && 'w-full',
        // Custom
        className,
      )}
      {...rest}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin shrink-0" aria-hidden="true" />
      ) : icon ? (
        <span className="shrink-0">{icon}</span>
      ) : null}
      {children && <span className="truncate">{children}</span>}
      {!loading && iconRight && <span className="shrink-0">{iconRight}</span>}
    </button>
  );
}
