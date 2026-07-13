import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Users, Eye, Heart, TrendingUp, Globe,
  Clock, User, Smartphone, Share2, Camera, MessageCircle,
  ExternalLink, Loader2, BarChart3, CalendarDays, Activity,
} from 'lucide-react';
import { api } from '../api/client';
import { useT } from '../i18n';

// ─── 类型定义 ──────────────────────────────────────────

interface TrendPoint {
  date: string;
  count: number;
}

interface SourceItem {
  source: string;
  count: number;
}

interface RecentVisitor {
  id: number;
  visitor_name: string;
  visitor_ip: string;
  source: string;
  page_viewed: string;
  duration: number;
  interested: boolean;
  visit_time: string;
}

interface StatsData {
  total_visits: number;
  interested_count: number;
  view_count: number;
  trend: TrendPoint[];
  source_distribution: SourceItem[];
  recent_visitors: RecentVisitor[];
}

// ─── 工具函数 ──────────────────────────────────────────

function formatTime(iso: string | null, t: (key: string, vars?: Record<string, string | number>) => string): string {
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

function formatDuration(sec: number, t: (key: string, vars?: Record<string, string | number>) => string): string {
  if (sec < 60) return t('analytics.duration.seconds', { n: sec });
  return t('analytics.duration.minutes', { n: Math.floor(sec / 60), m: sec % 60 });
}

function formatDateLabel(iso: string): string {
  const d = new Date(iso);
  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  return `${d.getMonth() + 1}/${d.getDate()} 周${weekdays[d.getDay()]}`;
}

const SOURCE_ICONS: Record<string, typeof Share2> = {
  direct: Globe,
  qrcode: Camera,
  share: Share2,
  scan: Smartphone,
};

const SOURCE_LABELS: Record<string, string> = {
  direct: 'analytics.source.direct',
  qrcode: 'analytics.source.qrcode',
  share: 'analytics.source.share',
  scan: 'analytics.source.scan',
};

const SOURCE_COLORS: Record<string, string> = {
  direct: 'bg-sky-500',
  qrcode: 'bg-violet-500',
  share: 'bg-emerald-500',
  scan: 'bg-amber-500',
};

// ─── 柱状图组件（纯CSS） ──────────────────────────────

function TrendBarChart({ data }: { data: TrendPoint[] }) {
  const maxVal = Math.max(...data.map(d => d.count), 1);

  return (
    <div className="flex items-end gap-2 h-36 px-1">
      {data.map((point) => {
        const pct = (point.count / maxVal) * 100;
        const isToday = new Date(point.date).toDateString() === new Date().toDateString();
        return (
          <div key={point.date} className="flex-1 flex flex-col items-center gap-1 group relative">
            <span className="text-xs font-semibold text-on-surface opacity-0 group-hover:opacity-100 transition-opacity">
              {point.count}
            </span>
            <div
              className={`w-full rounded-t-md transition-all duration-300 cursor-pointer ${
                isToday ? 'bg-primary' : 'bg-primary/40 hover:bg-primary/70'
              }`}
              style={{ height: `${Math.max(pct, 4)}%` }}
            />
            <span className="text-[10px] text-text-muted whitespace-nowrap">
              {new Date(point.date).getDate()}/{new Date(point.date).getMonth() + 1}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ─── 环形图组件（纯CSS） ──────────────────────────────

function DonutChart({ data, t }: { data: SourceItem[]; t: (key: string, vars?: Record<string, string | number>) => string }) {
  const total = data.reduce((s, i) => s + i.count, 0) || 1;
  let cumulative = 0;
  const segments = data.map((item) => {
    const start = cumulative;
    cumulative += (item.count / total) * 360;
    return { ...item, start, end: cumulative };
  });

  return (
    <div className="flex flex-col items-center gap-4">
      <svg width="140" height="140" viewBox="0 0 36 36" className="-rotate-90">
        {segments.map((seg, idx) => {
          const [x1, y1] = polarToCartesian(18, 18, 14, seg.start);
          const [x2, y2] = polarToCartesian(18, 18, 14, seg.end);
          const largeArc = seg.end - seg.start > 180 ? 1 : 0;
          const color = SOURCE_COLORS[seg.source] || 'bg-slate-400';
          // Map tailwind class to SVG color
          const fillMap: Record<string, string> = {
            'bg-sky-500': '#0ea5e9',
            'bg-violet-500': '#8b5cf6',
            'bg-emerald-500': '#10b981',
            'bg-amber-500': '#f59e0b',
            'bg-slate-400': '#94a3b8',
          };
          return (
            <path
              key={seg.source}
              d={`M ${x1} ${y1} A 14 14 0 ${largeArc} 1 ${x2} ${y2} L 18 18 Z`}
              fill={fillMap[color] || '#94a3b8'}
            />
          );
        })}
      </svg>
      <div className="flex flex-wrap gap-3 justify-center">
        {data.map((item) => (
          <div key={item.source} className="flex items-center gap-1.5 text-xs text-on-surface">
            <span className={`w-2.5 h-2.5 rounded-full ${SOURCE_COLORS[item.source] || 'bg-slate-400'}`} />
            {t(SOURCE_LABELS[item.source]) || item.source}
            <span className="font-semibold ml-1">{item.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number): [number, number] {
  const rad = (angleDeg * Math.PI) / 180;
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
}

// ─── 主组件 ────────────────────────────────────────────

export default function AnalyticsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const t = useT();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState<StatsData | null>(null);
  const [brochureName, setBrochureName] = useState('');

  const fetchStats = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.get(`/api/visitors/${id}/stats`);
      if (res.code === 200 && res.data) {
        setStats(res.data as StatsData);
        // Try to fetch brochure name
        const brRes = await api.get(`/api/v1/brochures/${id}`);
        if (brRes.code === 200 && brRes.data) {
          setBrochureName((brRes.data as any).name || (brRes.data as any).title || '');
        }
      } else {
        setError(res.message || t('analytics.fetchFailed'));
      }
    } catch (e: any) {
      setError(e.message || t('analytics.networkError'));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-bg flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
          <p className="text-sm text-text-muted">{t('analytics.loading')}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-neutral-bg flex items-center justify-center p-4">
        <div className="bg-surface rounded-2xl shadow-sm p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-error/10 flex items-center justify-center">
            <Activity className="w-8 h-8 text-error" />
          </div>
          <h2 className="text-lg font-semibold text-on-surface mb-2">{t('analytics.error.title')}</h2>
          <p className="text-sm text-text-muted mb-4">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-xl text-sm font-medium hover:bg-primary-container transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {t('analytics.back')}
          </button>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  const maxTrend = Math.max(...stats.trend.map(t => t.count), 1);

  return (
    <div className="min-h-screen bg-neutral-bg">
      {/* ── 顶栏 ── */}
      <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-lg border-b border-border-light">
        <div className="max-w-3xl mx-auto px-4 h-14 flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="p-2 -ml-2 rounded-xl hover:bg-neutral-bg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-on-surface" />
          </button>
          <div className="flex-1 min-w-0">
            <h1 className="text-base font-semibold text-on-surface truncate">
              {t('analytics.title')}
            </h1>
            {brochureName && (
              <p className="text-xs text-text-muted truncate">{brochureName}</p>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6 space-y-5 pb-24">
        {/* ── 概览卡片 ── */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-surface rounded-2xl shadow-sm p-4 text-center">
            <div className="w-10 h-10 mx-auto mb-2 rounded-xl bg-primary/10 flex items-center justify-center">
              <Eye className="w-5 h-5 text-primary" />
            </div>
            <p className="text-2xl font-bold text-on-surface">{stats.view_count}</p>
            <p className="text-xs text-text-muted mt-0.5">{t('analytics.views')}</p>
          </div>
          <div className="bg-surface rounded-2xl shadow-sm p-4 text-center">
            <div className="w-10 h-10 mx-auto mb-2 rounded-xl bg-emerald-500/10 flex items-center justify-center">
              <Users className="w-5 h-5 text-emerald-500" />
            </div>
            <p className="text-2xl font-bold text-on-surface">{stats.total_visits}</p>
            <p className="text-xs text-text-muted mt-0.5">{t('analytics.visitors')}</p>
          </div>
          <div className="bg-surface rounded-2xl shadow-sm p-4 text-center">
            <div className="w-10 h-10 mx-auto mb-2 rounded-xl bg-rose-500/10 flex items-center justify-center">
              <Heart className="w-5 h-5 text-rose-500" />
            </div>
            <p className="text-2xl font-bold text-on-surface">{stats.interested_count}</p>
            <p className="text-xs text-text-muted mt-0.5">{t('analytics.interests')}</p>
          </div>
        </div>

        {/* ── 趋势图 ── */}
        <div className="bg-surface rounded-2xl shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-semibold text-on-surface">{t('analytics.trend.title')}</h2>
          </div>
          <TrendBarChart data={stats.trend} />
          {/* 极简统计线 */}
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-border-light text-xs text-text-muted">
            <span>{t('analytics.trend.dailyAvg', { n: Math.round(stats.trend.reduce((s, t) => s + t.count, 0) / 7) })}</span>
            <span>{t('analytics.trend.peak', { n: maxTrend })}</span>
          </div>
        </div>

        {/* ── 来源分布 ── */}
        <div className="bg-surface rounded-2xl shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-4 h-5 text-primary" />
            <h2 className="text-sm font-semibold text-on-surface">{t('analytics.source.title')}</h2>
          </div>
          {stats.source_distribution.length > 0 ? (
            <DonutChart data={stats.source_distribution} t={t} />
          ) : (
            <p className="text-sm text-text-muted text-center py-6">{t('analytics.source.empty')}</p>
          )}
        </div>

        {/* ── 访客时间线 ── */}
        <div className="bg-surface rounded-2xl shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-semibold text-on-surface">{t('analytics.visitor.title')}</h2>
            <span className="ml-auto text-xs text-text-muted">
              {t('analytics.visitor.total', { n: stats.total_visits })}
            </span>
          </div>

          {stats.recent_visitors.length > 0 ? (
            <div className="space-y-0 divide-y divide-border-light">
              {stats.recent_visitors.map((v, idx) => {
                const SourceIcon = SOURCE_ICONS[v.source] || Globe;
                return (
                  <div key={v.id} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
                    {/* 时间线圆点 */}
                    <div className="relative flex flex-col items-center">
                      <div className={`w-2.5 h-2.5 rounded-full mt-1.5 ${
                        v.interested ? 'bg-rose-500' : 'bg-primary/60'
                      }`} />
                      {idx < stats.recent_visitors.length - 1 && (
                        <div className="w-px flex-1 bg-border-light mt-1" />
                      )}
                    </div>

                    {/* 内容 */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-on-surface truncate">
                          {v.visitor_name}
                        </span>
                        {v.interested && (
                          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full bg-rose-500/10 text-rose-600 text-[10px] font-medium">
                            <MessageCircle className="w-3 h-3" />
                            {t('analytics.visitor.interested')}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-0.5 text-xs text-text-muted">
                        <span className="flex items-center gap-1">
                          <SourceIcon className="w-3 h-3" />
                          {t(SOURCE_LABELS[v.source]) || v.source}
                        </span>
                        {v.duration > 0 && (
                          <span>{formatDuration(v.duration, t)}</span>
                        )}
                        <span>{formatTime(v.visit_time, t)}</span>
                      </div>
                      {v.page_viewed && (
                        <p className="text-xs text-text-muted/70 mt-0.5 truncate">
                          {t('analytics.visitor.viewed', { page: v.page_viewed })}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8">
              <Users className="w-10 h-10 text-text-muted/30 mx-auto mb-2" />
              <p className="text-sm text-text-muted">{t('analytics.visitor.empty')}</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
