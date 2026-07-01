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

function formatTime(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return '刚刚';
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}天前`;
  return d.toLocaleDateString('zh-CN');
}

function formatDuration(sec: number): string {
  if (sec < 60) return `${sec}秒`;
  return `${Math.floor(sec / 60)}分${sec % 60}秒`;
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
  direct: '直接访问',
  qrcode: '二维码',
  share: '分享链接',
  scan: '扫码',
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

function DonutChart({ data }: { data: SourceItem[] }) {
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
            {SOURCE_LABELS[item.source] || item.source}
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
        setError(res.message || t('获取统计数据失败'));
      }
    } catch (e: any) {
      setError(e.message || t('网络错误'));
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
          <p className="text-sm text-text-muted">{t('加载访客数据中...')}</p>
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
          <h2 className="text-lg font-semibold text-on-surface mb-2">{t('数据加载失败')}</h2>
          <p className="text-sm text-text-muted mb-4">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-xl text-sm font-medium hover:bg-primary-container transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {t('返回')}
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
              {t('访客分析')}
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
            <p className="text-xs text-text-muted mt-0.5">{t('浏览次数')}</p>
          </div>
          <div className="bg-surface rounded-2xl shadow-sm p-4 text-center">
            <div className="w-10 h-10 mx-auto mb-2 rounded-xl bg-emerald-500/10 flex items-center justify-center">
              <Users className="w-5 h-5 text-emerald-500" />
            </div>
            <p className="text-2xl font-bold text-on-surface">{stats.total_visits}</p>
            <p className="text-xs text-text-muted mt-0.5">{t('访客数')}</p>
          </div>
          <div className="bg-surface rounded-2xl shadow-sm p-4 text-center">
            <div className="w-10 h-10 mx-auto mb-2 rounded-xl bg-rose-500/10 flex items-center justify-center">
              <Heart className="w-5 h-5 text-rose-500" />
            </div>
            <p className="text-2xl font-bold text-on-surface">{stats.interested_count}</p>
            <p className="text-xs text-text-muted mt-0.5">{t('兴趣数')}</p>
          </div>
        </div>

        {/* ── 趋势图 ── */}
        <div className="bg-surface rounded-2xl shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-semibold text-on-surface">{t('近7天访问趋势')}</h2>
          </div>
          <TrendBarChart data={stats.trend} />
          {/* 极简统计线 */}
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-border-light text-xs text-text-muted">
            <span>{t('日均')} {Math.round(stats.trend.reduce((s, t) => s + t.count, 0) / 7)} {t('次')}</span>
            <span>{t('峰值')} {maxTrend} {t('次')}</span>
          </div>
        </div>

        {/* ── 来源分布 ── */}
        <div className="bg-surface rounded-2xl shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-4 h-5 text-primary" />
            <h2 className="text-sm font-semibold text-on-surface">{t('访客来源分布')}</h2>
          </div>
          {stats.source_distribution.length > 0 ? (
            <DonutChart data={stats.source_distribution} />
          ) : (
            <p className="text-sm text-text-muted text-center py-6">{t('暂无数据')}</p>
          )}
        </div>

        {/* ── 访客时间线 ── */}
        <div className="bg-surface rounded-2xl shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-semibold text-on-surface">{t('最近访客')}</h2>
            <span className="ml-auto text-xs text-text-muted">
              {t('共')} {stats.total_visits} {t('人')}
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
                            {t('有意向')}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-0.5 text-xs text-text-muted">
                        <span className="flex items-center gap-1">
                          <SourceIcon className="w-3 h-3" />
                          {SOURCE_LABELS[v.source] || v.source}
                        </span>
                        {v.duration > 0 && (
                          <span>{formatDuration(v.duration)}</span>
                        )}
                        <span>{formatTime(v.visit_time)}</span>
                      </div>
                      {v.page_viewed && (
                        <p className="text-xs text-text-muted/70 mt-0.5 truncate">
                          {t('浏览:')} {v.page_viewed}
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
              <p className="text-sm text-text-muted">{t('暂无访客记录')}</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
