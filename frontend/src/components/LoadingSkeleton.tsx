import React from 'react';
import { useT } from '../i18n';

// ─── 通用骨架元素 ──────────────────────────────────────

/** 矩形骨架块 */
function SkeletonBlock({ className = '' }: { className?: string }) {
  return <div className={`skeleton rounded-lg ${className}`} />;
}

/** 圆形骨架 */
function SkeletonCircle({ size = 'w-10 h-10' }: { size?: string }) {
  return <div className={`skeleton rounded-full ${size}`} />;
}

/** 文字行骨架 */
function SkeletonText({ width = 'w-full', className = '' }: { width?: string; className?: string }) {
  return <SkeletonBlock className={`h-3 ${width} ${className}`} />;
}

// ─── 卡片模式 ──────────────────────────────────────────

/**
 * 卡片模式骨架屏
 * 用于名片卡片列表项、定价卡片等
 */
export function CardSkeleton({ count = 1 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-surface rounded-2xl border border-border-light p-5 space-y-4"
        >
          {/* Avatar + Title row */}
          <div className="flex items-start gap-3">
            <SkeletonCircle size="w-12 h-12" />
            <div className="flex-1 space-y-2 pt-1">
              <SkeletonText width="w-2/3" />
              <SkeletonText width="w-1/2" className="h-2.5" />
            </div>
            <SkeletonBlock className="w-5 h-5" />
          </div>
          {/* Meta row */}
          <div className="flex gap-4">
            <SkeletonText width="w-20" className="h-2.5" />
            <SkeletonText width="w-24" className="h-2.5" />
          </div>
        </div>
      ))}
    </>
  );
}

// ─── 列表模式 ──────────────────────────────────────────

/**
 * 列表模式骨架屏
 * 用于团队成员列表、访客列表、匹配结果列表等
 */
export function ListSkeleton({ rows = 5, avatar = true }: { rows?: number; avatar?: boolean }) {
  return (
    <div className="divide-y divide-border-light">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-start gap-3 py-4 first:pt-0 last:pb-0">
          {avatar && <SkeletonCircle size="w-10 h-10" />}
          <div className="flex-1 space-y-2 min-w-0">
            <div className="flex items-center gap-2">
              <SkeletonText width="w-1/3" />
              <SkeletonBlock className="w-14 h-5 rounded-full" />
            </div>
            <SkeletonText width="w-1/2" className="h-2.5" />
            <SkeletonText width="w-3/4" className="h-2.5" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── 详情模式 ──────────────────────────────────────────

/**
 * 详情页骨架屏
 * 用于名片详情页、团队详情页、分析页面等
 */
export function DetailSkeleton({ fields = 4 }: { fields?: number }) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <SkeletonBlock className="w-10 h-10" />
        <div className="space-y-2 flex-1">
          <SkeletonText width="w-40" className="h-5" />
          <SkeletonText width="w-24" className="h-3" />
        </div>
      </div>

      {/* Profile card */}
      <div className="bg-surface rounded-2xl border border-border-light p-5 space-y-4">
        <div className="flex items-center gap-4">
          <SkeletonCircle size="w-16 h-16" />
          <div className="space-y-2 flex-1">
            <SkeletonText width="w-1/2" className="h-5" />
            <SkeletonText width="w-1/3" className="h-3" />
          </div>
        </div>
        <div className="border-t border-border-light pt-4 space-y-3">
          {Array.from({ length: fields }).map((_, i) => (
            <div key={i} className="flex items-center gap-2">
              <SkeletonBlock className="w-4 h-4" />
              <SkeletonText width={i % 2 === 0 ? 'w-2/3' : 'w-1/2'} className="h-3.5" />
            </div>
          ))}
        </div>
      </div>

      {/* Stats cards (for analytics) */}
      <div className="grid grid-cols-3 gap-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="bg-surface rounded-2xl border border-border-light p-4 space-y-2">
            <SkeletonBlock className="w-10 h-10 mx-auto rounded-xl" />
            <SkeletonText width="w-3/4" className="h-6 mx-auto" />
            <SkeletonText width="w-1/2" className="h-2.5 mx-auto" />
          </div>
        ))}
      </div>

      {/* Chart area */}
      <div className="bg-surface rounded-2xl border border-border-light p-5 space-y-3">
        <div className="flex items-center gap-2">
          <SkeletonBlock className="w-4 h-4" />
          <SkeletonText width="w-32" className="h-4" />
        </div>
        <SkeletonBlock className="w-full h-36" />
      </div>
    </div>
  );
}

// ─── 页面级骨架屏 ──────────────────────────────────────

/**
 * 全页骨架屏
 * 用一个可选的 title 来区分不同页面的加载状态
 */
export function PageSkeleton({
  mode = 'card',
  title,
  count = 3,
  rows = 5,
  fields = 4,
}: {
  mode?: 'card' | 'list' | 'detail';
  title?: string;
  count?: number;
  rows?: number;
  fields?: number;
}) {
  const t = useT();
  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      {title && (
        <div className="text-center mb-4">
          <SkeletonBlock className="w-16 h-16 mx-auto rounded-2xl mb-3" />
          <SkeletonText width="w-40" className="h-6 mx-auto" />
          <SkeletonText width="w-32" className="h-3 mx-auto mt-2" />
        </div>
      )}

      {mode === 'card' && <CardSkeleton count={count} />}
      {mode === 'list' && <ListSkeleton rows={rows} />}
      {mode === 'detail' && <DetailSkeleton fields={fields} />}
    </div>
  );
}

// ─── 默认导出 ──────────────────────────────────────────

export default PageSkeleton;
