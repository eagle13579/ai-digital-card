import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users, Loader2, User, ArrowLeft, Trash2, Eye,
  Clock, Search, X,
} from 'lucide-react';
import { api } from '../api/client';
import { useT } from '../i18n';

// ============================================================
// 类型定义
// ============================================================
interface TrustNetworkUser {
  id: number;
  name: string;
  company?: string;
  position?: string;
  avatar_url?: string;
}

interface VisitorRecord {
  id: number;
  visitor_name?: string;
  visitor_company?: string;
  viewed_at: string;
}

// ============================================================
// 辅助函数
// ============================================================
function formatDate(dateStr?: string, t?: (key: string, vars?: Record<string, string | number>) => string): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return t ? t('network.justNow') : '刚刚';
    if (minutes < 60) return t ? t('network.minutesAgo', { n: minutes }) : `${minutes}分钟前`;
    if (hours < 24) return t ? t('network.hoursAgo', { n: hours }) : `${hours}小时前`;
    if (days < 30) return t ? t('network.daysAgo', { n: days }) : `${days}天前`;

    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  } catch {
    return dateStr || '';
  }
}

// ============================================================
// 信任网络页面
// ============================================================
export default function NetworkPage() {
  const navigate = useNavigate();
  const t = useT();

  const [trustNetwork, setTrustNetwork] = useState<TrustNetworkUser[]>([]);
  const [trustNetworkLoading, setTrustNetworkLoading] = useState(false);

  const [visitors, setVisitors] = useState<VisitorRecord[]>([]);
  const [visitorsLoading, setVisitorsLoading] = useState(false);

  const [selectedCardId, setSelectedCardId] = useState<number | null>(null);
  const [cardList, setCardList] = useState<{ id: number; name: string }[]>([]);

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }, []);

  // ============================================================
  // 加载名片列表（用于选择查看信任网络）
  // ============================================================
  useEffect(() => {
    const fetchCardList = async () => {
      try {
        const res = await api.get('/api/v1/brochure/list');
        if (res.code === 200) {
          const items = Array.isArray(res.data) ? res.data : (res.data as any)?.items || [];
          setCardList(items.map((item: any) => ({ id: item.id, name: item.fields?.name || item.name || t('network.unnamed') })));
          if (items.length > 0 && !selectedCardId) {
            setSelectedCardId(items[0].id);
          }
        }
      } catch {}
    };
    fetchCardList();
  }, []);

  // ============================================================
  // 加载信任网络 & 访客记录
  // ============================================================
  const fetchTrustNetwork = useCallback(async (id: number) => {
    setTrustNetworkLoading(true);
    try {
      const res = await api.get(`/api/v1/brochures/${id}/trust_network`);
      if (res.code === 200 && Array.isArray(res.data)) {
        setTrustNetwork(res.data as TrustNetworkUser[]);
      } else {
        setTrustNetwork([]);
      }
    } catch {
      setTrustNetwork([]);
    } finally {
      setTrustNetworkLoading(false);
    }
  }, []);

  const fetchVisitors = useCallback(async (id: number) => {
    setVisitorsLoading(true);
    try {
      const res = await api.get(`/api/v1/brochure/${id}/visitors`);
      if (res.code === 200 && Array.isArray(res.data)) {
        setVisitors(res.data as VisitorRecord[]);
      } else {
        setVisitors([]);
      }
    } catch {
      setVisitors([]);
    } finally {
      setVisitorsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedCardId) {
      fetchTrustNetwork(selectedCardId);
      fetchVisitors(selectedCardId);
    }
  }, [selectedCardId, fetchTrustNetwork, fetchVisitors]);

  // ============================================================
  // 移除信任用户
  // ============================================================
  const handleRemoveTrust = async (trustedUserId: number) => {
    if (!selectedCardId) return;
    try {
      const res = await api.delete(`/api/v1/brochures/${selectedCardId}/trust_network?trusted_user_id=${trustedUserId}`);
      if (res.code === 200) {
        showToast(t('network.removeSuccess'), 'success');
        fetchTrustNetwork(selectedCardId);
      } else {
        showToast(t('network.removeFailed'), 'error');
      }
    } catch {
      showToast(t('network.removeFailed'), 'error');
    }
  };

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
          <button onClick={() => setToast(null)} className="ml-2 underline">{t('network.close')}</button>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-primary/10">
          <Users className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-on-surface">{t('network.title')}</h2>
          <p className="text-xs text-text-muted">{t('network.subtitle')}</p>
        </div>
      </div>

      {/* 名片选择 */}
      {cardList.length > 0 && (
        <div className="flex gap-2 overflow-x-auto overflow-hidden pb-1">
          {cardList.map((card) => (
            <button key={card.id} onClick={() => setSelectedCardId(card.id)}
              className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                selectedCardId === card.id
                  ? 'bg-primary text-white'
                  : 'bg-slate-100 text-text-muted hover:bg-slate-200'
              }`}
            >
              {card.name}
            </button>
          ))}
        </div>
      )}

      {/* 信任网络列表 */}
      <div className="bg-white rounded-2xl p-4 border border-border-light">
        <h3 className="text-sm font-bold text-on-surface mb-3 flex items-center gap-2">
          <Users className="w-4 h-4 text-primary" />
          {t('network.trustUsers')}
          {trustNetwork.length > 0 && <span className="text-xs text-text-muted font-normal">({trustNetwork.length})</span>}
        </h3>

        {trustNetworkLoading ? (
          <div className="flex items-center justify-center py-8"><Loader2 className="w-6 h-6 text-primary animate-spin" /></div>
        ) : !selectedCardId ? (
          <p className="text-xs text-text-muted text-center py-8">{t('network.selectCardFirst')}</p>
        ) : trustNetwork.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-2">
              <Users className="w-6 h-6 text-text-muted" />
            </div>
            <p className="text-xs text-text-muted">{t('network.noTrustUsers')}</p>
            <p className="text-[10px] text-text-muted mt-0.5">{t('network.noTrustUsersDesc')}</p>
          </div>
        ) : (
          <div className="space-y-2">
            {trustNetwork.map((user) => (
              <div key={user.id} className="flex items-center justify-between bg-slate-50 rounded-xl p-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white text-sm font-bold shrink-0">
                    {(user.name || '?')[0]}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-on-surface truncate">{user.name}</p>
                    {(user.position || user.company) && (
                      <p className="text-xs text-text-muted truncate">{[user.position, user.company].filter(Boolean).join(' · ')}</p>
                    )}
                  </div>
                </div>
                <button onClick={() => handleRemoveTrust(user.id)}
                  className="p-2 rounded-lg text-rose-500 hover:bg-rose-50 transition-colors shrink-0"
                  title={t('network.removeTrust')}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 访客记录 */}
      <div className="bg-white rounded-2xl p-4 border border-border-light">
        <h3 className="text-sm font-bold text-on-surface mb-3 flex items-center gap-2">
          <Eye className="w-4 h-4 text-primary" />
          {t('network.visitors')}
          {visitors.length > 0 && <span className="text-xs text-text-muted font-normal">({visitors.length})</span>}
        </h3>

        {visitorsLoading ? (
          <div className="flex items-center justify-center py-8"><Loader2 className="w-6 h-6 text-primary animate-spin" /></div>
        ) : !selectedCardId ? (
          <p className="text-xs text-text-muted text-center py-8">{t('network.selectCardFirst')}</p>
        ) : visitors.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-2">
              <Eye className="w-6 h-6 text-text-muted" />
            </div>
            <p className="text-xs text-text-muted">{t('network.noVisitors')}</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {visitors.map((v) => (
              <div key={v.id} className="flex items-center gap-3 bg-slate-50 rounded-xl p-3">
                <div className="w-9 h-9 rounded-full bg-slate-200 flex items-center justify-center text-slate-500 text-xs font-bold shrink-0">
                  {(v.visitor_name || '访')[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-on-surface truncate">{v.visitor_name || t('network.anonymousVisitor')}</p>
                  {v.visitor_company && <p className="text-xs text-text-muted truncate">{v.visitor_company}</p>}
                </div>
                <span className="text-[10px] text-text-muted shrink-0">{formatDate(v.viewed_at, t)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
