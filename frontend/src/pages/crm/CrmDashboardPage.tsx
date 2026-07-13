import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users, UserPlus, Target, Trophy, TrendingUp,
  ArrowRight, RefreshCw, Loader2, X,
} from 'lucide-react';
import { api } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';

// ============================================================
// 类型定义
// ============================================================
interface CrmStats {
  total_contacts: number;
  new_this_month: number;
  total_deals: number;
  won_deals: number;
  [key: string]: any;
}

// ============================================================
// 统计卡片组件
// ============================================================
interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  trend?: { value: string; positive: boolean };
  color: string;
  onClick?: () => void;
}

function StatCard({ label, value, icon, trend, color, onClick }: StatCardProps) {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-2xl border border-border-light p-5 transition-all duration-200 hover:shadow-elevated hover:-translate-y-0.5 ${
        onClick ? 'cursor-pointer' : ''
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2.5 rounded-xl ${color}`}>
          {icon}
        </div>
        {trend && (
          <span className={`flex items-center gap-0.5 text-xs font-medium ${
            trend.positive ? 'text-emerald-600' : 'text-rose-600'
          }`}>
            <TrendingUp className={`w-3 h-3 ${trend.positive ? '' : 'rotate-180'}`} />
            {trend.value}
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-on-surface mb-0.5">{value}</p>
      <p className="text-xs text-text-muted">{label}</p>
    </div>
  );
}

// ============================================================
// CRM 仪表盘
// ============================================================
export default function CrmDashboardPage() {
  const navigate = useNavigate();

  // 数据状态
  const [stats, setStats] = useState<CrmStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // ============================================================
  // 加载统计数据
  // ============================================================
  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get<CrmStats>('/api/crm/stats');
      if (res.code === 200 && res.data) {
        setStats(res.data);
      } else {
        // 无数据时的后备值
        setStats({
          total_contacts: 0,
          new_this_month: 0,
          total_deals: 0,
          won_deals: 0,
        });
      }
    } catch (e: any) {
      console.error('获取CRM统计失败:', e);
      setError(e.message || '加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  // ============================================================
  // 渲染
  // ============================================================
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <Users className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-on-surface">CRM 仪表盘</h2>
            <p className="text-xs text-text-muted">查看客户关系管理核心数据</p>
          </div>
        </div>
        <button
          onClick={fetchStats}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium text-text-muted hover:bg-slate-100 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>刷新</span>
        </button>
      </div>

      {/* 加载状态 */}
      {loading ? (
        <div className="py-16">
          <LoadingSpinner size="md" label="加载统计数据..." />
        </div>
      ) : error ? (
        /* 错误状态 */
        <div className="py-12 text-center bg-white rounded-2xl border border-border-light">
          <div className="w-14 h-14 rounded-full bg-rose-50 flex items-center justify-center mx-auto mb-3">
            <X className="w-7 h-7 text-rose-500" />
          </div>
          <p className="text-sm font-medium text-on-surface">加载失败</p>
          <p className="text-xs text-text-muted mt-1">{error}</p>
          <button
            onClick={fetchStats}
            className="mt-4 px-4 py-2 rounded-xl bg-primary text-white text-xs font-medium hover:bg-primary-container transition-colors inline-flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            重试
          </button>
        </div>
      ) : (
        <>
          {/* 统计卡片网格 */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="总联系人数"
              value={stats?.total_contacts ?? 0}
              icon={<Users className="w-5 h-5 text-sky-600" />}
              color="bg-sky-50"
              onClick={() => navigate('/crm')}
            />
            <StatCard
              label="本月新增"
              value={stats?.new_this_month ?? 0}
              icon={<UserPlus className="w-5 h-5 text-emerald-600" />}
              color="bg-emerald-50"
              trend={stats?.new_this_month ? { value: `+${stats.new_this_month}`, positive: true } : undefined}
            />
            <StatCard
              label="销售机会"
              value={stats?.total_deals ?? 0}
              icon={<Target className="w-5 h-5 text-amber-600" />}
              color="bg-amber-50"
              onClick={() => navigate('/crm/pipeline')}
            />
            <StatCard
              label="成交数"
              value={stats?.won_deals ?? 0}
              icon={<Trophy className="w-5 h-5 text-purple-600" />}
              color="bg-purple-50"
              trend={stats?.won_deals ? { value: `${Math.round((stats.won_deals / (stats.total_deals || 1)) * 100)}%`, positive: true } : undefined}
            />
          </div>

          {/* 快捷操作 */}
          <div className="bg-white rounded-2xl border border-border-light p-5">
            <h3 className="text-sm font-bold text-on-surface mb-4">快捷操作</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                onClick={() => navigate('/crm')}
                className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 hover:bg-sky-50 hover:border-sky-200 border border-border-light transition-all group"
              >
                <div className="p-2 rounded-lg bg-sky-50">
                  <Users className="w-4 h-4 text-sky-600" />
                </div>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-on-surface">联系人管理</p>
                  <p className="text-[10px] text-text-muted">查看和管理所有联系人</p>
                </div>
                <ArrowRight className="w-4 h-4 text-text-muted group-hover:text-primary transition-colors" />
              </button>

              <button
                onClick={() => navigate('/crm/pipeline')}
                className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 hover:bg-amber-50 hover:border-amber-200 border border-border-light transition-all group"
              >
                <div className="p-2 rounded-lg bg-amber-50">
                  <Target className="w-4 h-4 text-amber-600" />
                </div>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-on-surface">销售管道</p>
                  <p className="text-[10px] text-text-muted">管理销售机会和阶段</p>
                </div>
                <ArrowRight className="w-4 h-4 text-text-muted group-hover:text-primary transition-colors" />
              </button>

              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 hover:bg-emerald-50 hover:border-emerald-200 border border-border-light transition-all group"
              >
                <div className="p-2 rounded-lg bg-emerald-50">
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                </div>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-on-surface">数据概览</p>
                  <p className="text-[10px] text-text-muted">返回主仪表盘</p>
                </div>
                <ArrowRight className="w-4 h-4 text-text-muted group-hover:text-primary transition-colors" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
