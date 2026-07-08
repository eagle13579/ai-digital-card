import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, Loader2, RefreshCw, ExternalLink,
  Search, Filter, ArrowUpDown, TrendingUp,
  Target, Package, CheckCircle2,
} from 'lucide-react';
import { api } from '../api/client';
import { useT } from '../i18n';

// ============================================================
// 类型定义
// ============================================================
interface MatchItem {
  type: 'need' | 'product';
  id: number;
  title: string;
  category?: string;
  score: number;
  reasons: string[];
}

interface CardListItem {
  id: number;
  name: string;
  fields?: { name?: string };
}

// ============================================================
// 匹配中心页面
// ============================================================
export default function MatchingPage() {
  const navigate = useNavigate();
  const t = useT();

  const [matchResults, setMatchResults] = useState<MatchItem[]>([]);
  const [matchLoading, setMatchLoading] = useState(false);
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null);
  const [cardList, setCardList] = useState<CardListItem[]>([]);
  const [filter, setFilter] = useState<'all' | 'need' | 'product'>('all');
  const [sortBy, setSortBy] = useState<'score' | 'title'>('score');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }, []);

  // ============================================================
  // 加载名片列表
  // ============================================================
  useEffect(() => {
    const fetchCardList = async () => {
      try {
        const res = await api.get('/api/v1/brochures');
        if (res.code === 200) {
          const items = Array.isArray(res.data) ? res.data : (res.data as any)?.items || [];
          setCardList(items);
          if (items.length > 0 && !selectedCardId) {
            setSelectedCardId(items[0].id);
          }
        }
      } catch {}
    };
    fetchCardList();
  }, []);

  // ============================================================
  // 执行匹配
  // ============================================================
  const handleMatch = useCallback(async () => {
    if (!selectedCardId) {
      showToast(t('match.selectCardFirst'), 'error');
      return;
    }

    setMatchLoading(true);
    setMatchResults([]);

    try {
      const res = await api.post<{ matches: any[]; total: number }>(
        '/api/v1/match/engine',
        { min_score: 0.3 }
      );

      if (res.code === 200 && res.data) {
        const items: MatchItem[] = (res.data.matches || []).map((m: any) => ({
          type: 'product' as const,
          id: m.user_id,
          title: m.user_name || '',
          category: m.user_company || '',
          score: m.score / 100,
          reasons: (m.common_tags || []).map((t: any) => typeof t === 'string' ? t : t.tag || ''),
        }));
        setMatchResults(items);
        if (items.length === 0) {
          showToast(t('match.noResults'), 'success');
        } else {
          showToast(t('match.foundResults', { n: items.length }), 'success');
        }
      } else {
        setMatchResults([]);
        showToast(t('match.failed'), 'error');
      }
    } catch {
      setMatchResults([]);
      showToast(t('match.requestFailed'), 'error');
    } finally {
      setMatchLoading(false);
    }
  }, [selectedCardId, showToast]);

  // ============================================================
  // 过滤 & 排序
  // ============================================================
  const filteredResults = matchResults
    .filter((item) => filter === 'all' || item.type === filter)
    .sort((a, b) => {
      if (sortBy === 'score') return b.score - a.score;
      return a.title.localeCompare(b.title);
    });

  const needCount = matchResults.filter((m) => m.type === 'need').length;
  const productCount = matchResults.filter((m) => m.type === 'product').length;

  // ============================================================
  // 渲染
  // ============================================================
  return (
    <div className="space-y-6 max-w-lg mx-auto">
      {/* Toast */}
      {toast && (
        <div className={`rounded-xl p-3 text-xs flex items-center justify-between ${
          toast.type === 'success' ? 'bg-emerald-50 border border-emerald-200 text-emerald-700' : 'bg-rose-50 border border-rose-200 text-rose-700'
        }`}>
          <span>{toast.message}</span>
          <button onClick={() => setToast(null)} className="ml-2 underline">{t('match.close')}</button>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-gradient-to-r from-amber-400 to-orange-500">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-on-surface">{t('match.title')}</h2>
          <p className="text-xs text-text-muted">{t('match.subtitle')}</p>
        </div>
      </div>

      {/* 名片选择 */}
      {cardList.length > 0 && (
        <div>
          <label className="block text-xs font-medium text-text-muted mb-2">{t('match.selectCard')}</label>
          <div className="flex gap-2 overflow-x-auto overflow-hidden pb-1">
            {cardList.map((card) => (
              <button key={card.id} onClick={() => setSelectedCardId(card.id)}
                className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  selectedCardId === card.id
                    ? 'bg-primary text-white'
                    : 'bg-slate-100 text-text-muted hover:bg-slate-200'
                }`}
              >
                {card.fields?.name || card.name || t('match.unnamed')}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 匹配按钮 */}
      <button onClick={handleMatch} disabled={matchLoading || !selectedCardId}
        className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-primary to-purple-600 text-white font-medium text-sm hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg shadow-primary/25"
      >
        {matchLoading ? (
          <><Loader2 className="w-5 h-5 animate-spin" /> {t('match.matching')}...</>
        ) : (
          <><Target className="w-5 h-5" /> {t('match.startMatch')}</>
        )}
      </button>

      {/* 概览统计 */}
      {matchResults.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white rounded-xl p-3 border border-border-light text-center">
            <p className="text-xl font-bold text-primary">{matchResults.length}</p>
            <p className="text-[10px] text-text-muted">{t('match.total')}</p>
          </div>
          <div className="bg-white rounded-xl p-3 border border-border-light text-center">
            <p className="text-xl font-bold text-amber-600">{needCount}</p>
            <p className="text-[10px] text-text-muted">{t('match.need')}</p>
          </div>
          <div className="bg-white rounded-xl p-3 border border-border-light text-center">
            <p className="text-xl font-bold text-blue-600">{productCount}</p>
            <p className="text-[10px] text-text-muted">{t('match.product')}</p>
          </div>
        </div>
      )}

      {/* 筛选 & 排序 */}
      {matchResults.length > 0 && (
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-100 rounded-xl p-0.5">
            {(['all', 'need', 'product'] as const).map((f) => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-[10px] text-xs font-medium transition-colors ${
                  filter === f ? 'bg-white text-on-surface shadow-sm' : 'text-text-muted hover:text-on-surface'
                }`}
              >
                {f === 'all' ? t('match.filterAll') : f === 'need' ? t('match.filterNeed') : t('match.filterProduct')}
              </button>
            ))}
          </div>
          <button onClick={() => setSortBy(sortBy === 'score' ? 'title' : 'score')}
            className="ml-auto px-3 py-1.5 rounded-xl bg-slate-100 text-xs text-text-muted hover:text-on-surface transition-colors flex items-center gap-1"
          >
            <ArrowUpDown className="w-3 h-3" />
            {sortBy === 'score' ? t('match.sortScore') : t('match.sortName')}
          </button>
        </div>
      )}

      {/* 匹配结果 */}
      {matchLoading ? (
        <div className="flex flex-col items-center py-16 gap-3">
          <Loader2 className="w-10 h-10 text-primary animate-spin" />
          <p className="text-sm text-text-muted">{t('match.analyzing')}...</p>
          <div className="w-48 h-1.5 bg-slate-200 rounded-full overflow-hidden">
            <div className="h-full bg-primary rounded-full animate-pulse" style={{ width: '60%' }} />
          </div>
        </div>
      ) : !selectedCardId ? (
        <div className="flex flex-col items-center py-16 gap-3">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center">
            <Search className="w-8 h-8 text-text-muted" />
          </div>
          <p className="text-sm text-text-muted">{t('match.selectCardFirst')}</p>
        </div>
      ) : filteredResults.length === 0 && matchResults.length > 0 ? (
        <div className="text-center py-8">
          <p className="text-xs text-text-muted">{t('match.noFilterResults')}</p>
        </div>
      ) : filteredResults.length === 0 ? (
        <div className="flex flex-col items-center py-16 gap-3">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center">
            <TrendingUp className="w-8 h-8 text-text-muted" />
          </div>
          <p className="text-sm font-medium text-on-surface">{t('match.noResults')}</p>
          <p className="text-xs text-text-muted text-center">{t('match.noResultsDesc1')}<br />{t('match.noResultsDesc2')}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredResults.map((item) => (
            <div key={`${item.type}-${item.id}`}
              className="bg-white rounded-2xl p-4 border border-border-light hover:shadow-md transition-all duration-200 cursor-pointer"
            >
              <div className="flex items-start gap-3">
                <span className={`px-2 py-1 rounded-lg text-[10px] font-medium shrink-0 ${
                  item.type === 'need' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
                }`}>
                  {item.type === 'need' ? t('match.need') : t('match.product')}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-bold text-on-surface truncate">{item.title}</p>
                  {item.category && (
                    <p className="text-xs text-text-muted mt-0.5">{item.category}</p>
                  )}
                  {/* 匹配度条 */}
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full transition-all ${
                        item.score >= 0.7 ? 'bg-green-500' : item.score >= 0.4 ? 'bg-amber-500' : 'bg-slate-300'
                      }`} style={{ width: `${Math.round(item.score * 100)}%` }} />
                    </div>
                    <span className={`text-xs font-medium shrink-0 ${
                      item.score >= 0.7 ? 'text-green-600' : item.score >= 0.4 ? 'text-amber-600' : 'text-text-muted'
                    }`}>
                      {Math.round(item.score * 100)}%
                    </span>
                  </div>
                  {/* 匹配理由 */}
                  {item.reasons && item.reasons.length > 0 && (
                    <div className="mt-2 space-y-0.5">
                      {item.reasons.slice(0, 2).map((r, i) => (
                        <p key={i} className="text-[10px] text-text-muted flex items-start gap-1">
                          <CheckCircle2 className="w-3 h-3 text-green-500 mt-0.5 shrink-0" />
                          {r}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
                <ExternalLink className="w-4 h-4 text-text-muted shrink-0 mt-1" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 提示 */}
      {matchResults.length > 0 && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-4 border border-blue-100">
          <div className="flex gap-2">
            <Lightbulb className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
            <div>
              <p className="text-xs font-medium text-on-surface">{t('match.suggestion')}</p>
              <p className="text-[10px] text-text-muted mt-0.5">
                {t('match.suggestionDesc')}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// 内联图标（避免缺失）
// ============================================================
function Lightbulb({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5C7.7 12.8 8 13.6 9 14" />
      <path d="M9 14h6" />
      <path d="M9 17h6" />
      <path d="M10 20h4" />
    </svg>
  );
}
