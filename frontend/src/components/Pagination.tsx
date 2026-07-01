import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import clsx from 'clsx';

// ============================================================
// 分页组件
// 支持: 页码切换、每页条数、总览统计、小型变体
// ============================================================

interface PaginationProps {
  /** 当前页（从 1 开始） */
  current: number;
  /** 总页数 */
  total: number;
  /** 总数条目 */
  totalItems?: number;
  /** 切换页回调 */
  onChange: (page: number) => void;
  /** 每页条数 */
  pageSize?: number;
  /** 每页条数选项 */
  pageSizeOptions?: number[];
  /** 切换每页条数回调 */
  onPageSizeChange?: (size: number) => void;
  /** 紧凑模式 */
  compact?: boolean;
  /** 禁用 */
  disabled?: boolean;
  /** 自定义类名 */
  className?: string;
}

/**
 * Pagination — 分页导航组件
 *
 * 显示页码控制、条目统计、每页条数切换，支持紧凑模式用于表格/列表底部。
 */
export default function Pagination({
  current,
  total,
  totalItems,
  onChange,
  pageSize = 10,
  pageSizeOptions = [10, 20, 50, 100],
  onPageSizeChange,
  compact = false,
  disabled = false,
  className,
}: PaginationProps) {
  if (total <= 0) return null;

  /** 计算可见页码列表 */
  const getVisiblePages = (): (number | 'ellipsis')[] => {
    const pages: (number | 'ellipsis')[] = [];
    const delta = compact ? 1 : 2;

    pages.push(1);

    if (current - delta > 2) pages.push('ellipsis');

    for (let i = Math.max(2, current - delta); i <= Math.min(total - 1, current + delta); i++) {
      pages.push(i);
    }

    if (current + delta < total - 1) pages.push('ellipsis');

    if (total > 1) pages.push(total);

    return pages;
  };

  const visiblePages = getVisiblePages();
  const from = totalItems ? (current - 1) * pageSize + 1 : undefined;
  const to = totalItems ? Math.min(current * pageSize, totalItems) : undefined;

  const btnBase = clsx(
    'inline-flex items-center justify-center rounded-lg text-sm font-medium',
    'transition-colors duration-150 select-none',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30',
    disabled && 'opacity-40 cursor-not-allowed pointer-events-none',
  );

  const pageBtn = (active: boolean) =>
    clsx(
      btnBase,
      active
        ? 'bg-primary text-white hover:bg-primary-container'
        : 'text-text-muted hover:text-on-surface hover:bg-slate-100',
    );

  const navBtn = (disabledBtn: boolean) =>
    clsx(
      btnBase,
      'text-text-muted hover:text-on-surface hover:bg-slate-100',
      disabledBtn && 'opacity-30 cursor-not-allowed',
    );

  const visiblePage = (page: number | 'ellipsis', idx: number) => {
    if (page === 'ellipsis') {
      return (
        <span
          key={`ellipsis-${idx}`}
          className="inline-flex items-center justify-center w-8 h-8 text-xs text-text-muted select-none"
        >
          …
        </span>
      );
    }

    const isActive = page === current;
    return (
      <button
        key={page}
        onClick={() => !disabled && onChange(page)}
        disabled={disabled || isActive}
        className={clsx(
          pageBtn(isActive),
          compact ? 'w-7 h-7 text-xs' : 'w-8 h-8 text-sm',
        )}
        aria-label={`第 ${page} 页`}
        aria-current={isActive ? 'page' : undefined}
      >
        {page}
      </button>
    );
  };

  return (
    <nav
      className={clsx(
        'flex items-center gap-2',
        compact ? 'flex-row' : 'flex-wrap',
        className,
      )}
      aria-label="分页导航"
    >
      {/* 条目统计 */}
      {totalItems !== undefined && !compact && (
        <span className="text-xs text-text-muted mr-2 whitespace-nowrap">
          共 {totalItems} 条
          {from && to && `（${from}-${to}）`}
        </span>
      )}

      {/* 首页 */}
      {!compact && (
        <button
          onClick={() => !disabled && onChange(1)}
          disabled={disabled || current === 1}
          className={navBtn(current === 1)}
          aria-label="首页"
        >
          <ChevronsLeft className="w-4 h-4" />
        </button>
      )}

      {/* 上一页 */}
      <button
        onClick={() => !disabled && onChange(current - 1)}
        disabled={disabled || current === 1}
        className={navBtn(current === 1)}
        aria-label="上一页"
      >
        <ChevronLeft className="w-4 h-4" />
      </button>

      {/* 页码 */}
      {compact ? (
        <span className="text-sm text-text-muted px-1 whitespace-nowrap">
          {current} / {total}
        </span>
      ) : (
        <div className="flex items-center gap-1">
          {visiblePages.map((p, i) => visiblePage(p, i))}
        </div>
      )}

      {/* 下一页 */}
      <button
        onClick={() => !disabled && onChange(current + 1)}
        disabled={disabled || current === total}
        className={navBtn(current === total)}
        aria-label="下一页"
      >
        <ChevronRight className="w-4 h-4" />
      </button>

      {/* 末页 */}
      {!compact && (
        <button
          onClick={() => !disabled && onChange(total)}
          disabled={disabled || current === total}
          className={navBtn(current === total)}
          aria-label="末页"
        >
          <ChevronsRight className="w-4 h-4" />
        </button>
      )}

      {/* 每页条数 */}
      {onPageSizeChange && !compact && (
        <div className="flex items-center gap-1.5 ml-3">
          <span className="text-xs text-text-muted">每页</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            disabled={disabled}
            className="text-xs border border-border-light rounded-lg px-2 py-1 bg-surface text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-40"
            aria-label="每页条数"
          >
            {pageSizeOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt} 条
              </option>
            ))}
          </select>
        </div>
      )}
    </nav>
  );
}
