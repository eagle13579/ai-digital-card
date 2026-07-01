import { Clock, Eye, FileText, Loader2, Plus, ChevronRight, User } from 'lucide-react';
import { useT } from '../i18n';

// ============================================================
// 类型定义（从 BusinessCardPage 提取）
// ============================================================

export interface CardFields {
  name?: string;
  position?: string;
  company?: string;
  phone?: string;
  email?: string;
  wechat?: string;
  address?: string;
  website?: string;
  cover_image?: string;
}

export interface CardListItem {
  id: number;
  name: string;
  fields: CardFields;
  cover_image?: string;
  created_at: string;
  view_count: number;
}

export interface BusinessCardListProps {
  /** 名片列表数据 */
  cards: CardListItem[];
  /** 是否正在加载 */
  loading: boolean;
  /** 点击名片的回调 */
  onSelect: (id: number) => void;
  /** 点击创建新名片的回调 */
  onCreateNew?: () => void;
}

// ============================================================
// 工具函数
// ============================================================

/** 格式化日期显示 */
function formatDate(dateStr?: string): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  } catch {
    return dateStr;
  }
}

// ============================================================
// BusinessCardList 组件
// ============================================================

/**
 * 名片列表组件
 *
 * 从 BusinessCardPage 提取的标准列表模板，展示了如何将页面中的列表部分
 * 拆分为独立的可复用组件。
 *
 * 支持三种状态：
 * - loading：加载中骨架屏
 * - empty：空列表引导创建
 * - normal：正常列表渲染
 */
export default function BusinessCardList({
  cards,
  loading,
  onSelect,
  onCreateNew,
}: BusinessCardListProps) {
  const t = useT();
  // ---- Loading 状态 ----
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4">
            <FileText className="w-8 h-8 text-primary" />
          </div>
          <h2 className="text-xl font-bold text-on-surface">{t('我的AI数智名片')}</h2>
        </div>
        <div className="flex flex-col items-center py-12 gap-3">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
          <p className="text-sm text-text-muted">{t('加载名片列表...')}</p>
        </div>
      </div>
    );
  }

  // ---- Empty 状态 ----
  if (cards.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4">
            <FileText className="w-8 h-8 text-primary" />
          </div>
          <h2 className="text-xl font-bold text-on-surface">{t('我的AI数智名片')}</h2>
          <p className="text-sm text-text-muted mt-1">{t('共')} 0 {t('张名片')}</p>
        </div>
        <div className="flex flex-col items-center py-12 gap-4">
          <div className="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center">
            <User className="w-10 h-10 text-text-muted" />
          </div>
          <div className="text-center">
            <p className="text-base font-medium text-on-surface">{t('暂无AI数智名片')}</p>
            <p className="text-sm text-text-muted mt-1">{t('点击下方按钮创建您的第一张名片')}</p>
          </div>
        </div>
        {onCreateNew && (
          <button
            onClick={onCreateNew}
            className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-primary to-purple-600 text-white font-medium text-sm hover:opacity-90 transition-opacity flex items-center justify-center gap-2 shadow-lg shadow-primary/25"
          >
            <Plus className="w-5 h-5" />
            {t('创建新名片')}
          </button>
        )}
      </div>
    );
  }

  // ---- 正常列表 ----
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4">
          <FileText className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-xl font-bold text-on-surface">{t('我的AI数智名片')}</h2>
        <p className="text-sm text-text-muted mt-1">
          {t('共')} {cards.length} {t('张名片')}
        </p>
      </div>

      {/* Card list */}
      <div className="space-y-3">
        {cards.map((card) => (
          <div
            key={card.id}
            onClick={() => onSelect(card.id)}
            className="bg-white rounded-2xl p-4 border border-border-light hover:shadow-md hover:border-primary/30 transition-all duration-200 cursor-pointer"
          >
            <div className="flex items-start gap-3">
              {/* Avatar */}
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-lg shrink-0">
                {(card.fields?.name || card.name || '?')[0]}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <h3 className="text-base font-bold text-on-surface truncate">
                  {card.fields?.name || card.name || '未命名'}
                </h3>
                <div className="flex items-center gap-2 mt-0.5 text-xs text-text-muted">
                  {card.fields?.position && (
                    <span className="truncate">{card.fields.position}</span>
                  )}
                  {card.fields?.position && card.fields?.company && (
                    <span>·</span>
                  )}
                  {card.fields?.company && (
                    <span className="truncate">{card.fields.company}</span>
                  )}
                </div>

                {/* Meta */}
                <div className="flex items-center gap-3 mt-2 text-[11px] text-text-muted">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDate(card.created_at)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Eye className="w-3 h-3" />
                    {card.view_count ?? 0} {t('次浏览')}
                  </span>
                </div>
              </div>

              {/* Arrow */}
              <ChevronRight className="w-5 h-5 text-text-muted shrink-0 mt-2" />
            </div>
          </div>
        ))}
      </div>

      {/* Create button */}
      {onCreateNew && (
        <button
          onClick={onCreateNew}
          className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-primary to-purple-600 text-white font-medium text-sm hover:opacity-90 transition-opacity flex items-center justify-center gap-2 shadow-lg shadow-primary/25"
        >
          <Plus className="w-5 h-5" />
          {t('创建新名片')}
        </button>
      )}
    </div>
  );
}
