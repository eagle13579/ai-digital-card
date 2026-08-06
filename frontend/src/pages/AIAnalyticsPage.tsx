import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3, GitFork, Lightbulb, Users, Activity, TrendingUp,
  Eye, MessageCircle, Bot, AlertCircle, RefreshCw, ArrowRight,
} from 'lucide-react';
import { useT } from '../i18n';
import { api } from '../api/client';

// ============================================================
// 类型定义
// ============================================================
interface HealthData {
  status: string;
  service: string;
  version: string;
}

interface AnalyticsState {
  loading: boolean;
  error: string | null;
  health: HealthData | null;
  backendOnline: boolean;
}

// ============================================================
// 模拟数据（作为后端不可用时的降级兜底）
// ============================================================
const MOCK_DATA = {
  cardOverview: {
    totalCards: 128,
    totalViews: 4560,
    activeContacts: 89,
    avgInterestRate: '68%',
  },
  network: {
    totalConnections: 342,
    mutualContacts: 156,
    networkGroups: 12,
    recentGrowth: '+23%',
  },
  recommendations: [
    { type: '潜在客户', name: '张伟', company: '星辰科技', match: '92%' },
    { type: '合作机会', name: '李明', company: '云帆数据', match: '88%' },
    { type: '人脉扩展', name: '王芳', company: '锐思咨询', match: '85%' },
  ],
};

// ============================================================
// 分析卡片组件
// ============================================================
interface AnalyticsCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  gradient: string;
  stats?: { label: string; value: string | number }[];
  children?: React.ReactNode;
}

function AnalyticsCard({ icon, title, description, gradient, stats, children }: AnalyticsCardProps) {
  return (
    <div className="bg-white rounded-2xl border border-border-light hover:shadow-md hover:border-primary/30 transition-all duration-200 overflow-hidden">
      {/* Header */}
      <div className={`${gradient} px-5 py-4 flex items-center gap-3`}>
        <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center shrink-0">
          <div className="text-white">{icon}</div>
        </div>
        <div>
          <h3 className="text-base font-bold text-white">{title}</h3>
          <p className="text-xs text-white/80 mt-0.5">{description}</p>
        </div>
      </div>

      {/* Body */}
      <div className="p-5">
        {stats && (
          <div className="grid grid-cols-2 gap-4 mb-4">
            {stats.map((s, i) => (
              <div key={i} className="text-center">
                <p className="text-xl font-bold text-on-surface">{s.value}</p>
                <p className="text-xs text-text-muted mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}

// ============================================================
// 智能推荐子组件
// ============================================================
function RecommendationList() {
  const t = useT();

  return (
    <div className="space-y-3">
      {MOCK_DATA.recommendations.map((rec, i) => (
        <div
          key={i}
          className="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center text-primary font-bold text-sm shrink-0">
              {rec.name[0]}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-on-surface truncate">{rec.name}</p>
              <p className="text-xs text-text-muted truncate">{rec.type} · {rec.company}</p>
            </div>
          </div>
          <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg shrink-0 ml-2">
            {rec.match}
          </span>
        </div>
      ))}
      <button className="w-full text-center text-xs text-primary font-medium py-2 hover:underline">
        {t('查看全部推荐 →')}
      </button>
    </div>
  );
}

// ============================================================
// 人脉关系网络子组件
// ============================================================
function NetworkOverview() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-text-muted">总连接数</span>
        <span className="font-bold text-on-surface">{MOCK_DATA.network.totalConnections}</span>
      </div>
      <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-primary to-purple-500 rounded-full"
          style={{ width: '65%' }}
        />
      </div>
      <div className="flex items-center justify-between text-xs text-text-muted">
        <span className="flex items-center gap-1">
          <Users className="w-3 h-3" />
          共同联系人 {MOCK_DATA.network.mutualContacts}
        </span>
        <span className="flex items-center gap-1">
          <Activity className="w-3 h-3" />
          增长 {MOCK_DATA.network.recentGrowth}
        </span>
      </div>
    </div>
  );
}

// ============================================================
// Loading 骨架屏
// ============================================================
function LoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white rounded-2xl border border-border-light overflow-hidden animate-pulse">
          <div className="h-16 bg-slate-200" />
          <div className="p-5 space-y-3">
            <div className="grid grid-cols-2 gap-4">
              {[1, 2, 3, 4].map((j) => (
                <div key={j} className="text-center space-y-1">
                  <div className="h-6 bg-slate-200 rounded w-12 mx-auto" />
                  <div className="h-3 bg-slate-100 rounded w-16 mx-auto" />
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ============================================================
// 错误状态提示
// ============================================================
function ErrorBanner({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-center gap-3">
      <AlertCircle className="w-5 h-5 text-red-500 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-red-700">后端连接异常</p>
        <p className="text-xs text-red-500 mt-0.5 truncate">{message}</p>
      </div>
      <button
        onClick={onRetry}
        className="flex items-center gap-1.5 text-sm font-medium text-red-600 hover:text-red-700 bg-red-100 hover:bg-red-200 px-3 py-1.5 rounded-lg transition-colors shrink-0"
      >
        <RefreshCw className="w-3.5 h-3.5" />
        重试
      </button>
    </div>
  );
}

// ============================================================
// 后端连通性指示器
// ============================================================
function BackendStatus({ online, health }: { online: boolean; health: HealthData | null }) {
  if (!health) return null;
  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
      online
        ? 'bg-emerald-50 text-emerald-600'
        : 'bg-red-50 text-red-600'
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${online ? 'bg-emerald-500' : 'bg-red-500'}`} />
      {online ? `后端在线 v${health.version}` : '后端离线'}
    </div>
  );
}

// ============================================================
// AI对话快捷入口卡片
// ============================================================
function AiChatQuickEntry() {
  const navigate = useNavigate();

  const handleOpenChat = () => {
    // 打开AI对话 — 直接跳转到对话页面或打开一个弹窗
    // 目前路由表中尚无独立 /ai-chat 页面，我们可以导航到 /
    // 并在控制台提示，或使用 window.open 打开后端聊天端点
    window.open('/api/v1/ai/chat', '_blank');
  };

  return (
    <div className="bg-white rounded-2xl border border-border-light hover:shadow-md hover:border-primary/30 transition-all duration-200 overflow-hidden group">
      {/* Header */}
      <div className="bg-gradient-to-br from-indigo-500 to-indigo-700 px-5 py-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center shrink-0">
          <Bot className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-base font-bold text-white">AI 对话</h3>
          <p className="text-xs text-white/80 mt-0.5">智能知识问答与业务助手</p>
        </div>
      </div>

      {/* Body */}
      <div className="p-5">
        <p className="text-sm text-text-muted mb-4">
          基于RAG技术的智能对话引擎，可查询名片信息、业务数据、行业知识等。
        </p>
        <div className="space-y-2 mb-4">
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <div className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
            RAG 增强检索，答案更精准
          </div>
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <div className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
            支持连续对话，记忆上下文
          </div>
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <div className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
            数据安全，私有化部署
          </div>
        </div>
        <button
          onClick={handleOpenChat}
          className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white text-sm font-semibold py-2.5 rounded-xl transition-all duration-200 group-hover:shadow-md"
        >
          <MessageCircle className="w-4 h-4" />
          开始对话
          <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  );
}

// ============================================================
// 主组件
// ============================================================
export default function AIAnalyticsPage() {
  const t = useT();
  const [state, setState] = useState<AnalyticsState>({
    loading: true,
    error: null,
    health: null,
    backendOnline: false,
  });

  const fetchHealth = async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const res = await api.get<HealthData>('/api/health');
      if (res.code === 200 && res.data) {
        setState({
          loading: false,
          error: null,
          health: res.data,
          backendOnline: res.data.status === 'ok',
        });
      } else {
        setState((prev) => ({
          ...prev,
          loading: false,
          error: res.message || '后端返回异常状态',
          backendOnline: false,
        }));
      }
    } catch (e: any) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: e.message || '无法连接到后端服务',
        backendOnline: false,
      }));
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-on-surface flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-primary" />
            AI 智能分析
          </h1>
          <p className="text-sm text-text-muted mt-1">
            基于AI的智能数据分析和人脉管理建议
          </p>
        </div>
        <BackendStatus online={state.backendOnline} health={state.health} />
      </div>

      {/* 加载状态 */}
      {state.loading && <LoadingSkeleton />}

      {/* 错误状态 */}
      {!state.loading && state.error && (
        <ErrorBanner message={state.error} onRetry={fetchHealth} />
      )}

      {/* 后端离线提示（非错误状态下显示） */}
      {!state.loading && !state.error && !state.backendOnline && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-amber-500 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-amber-700">后端服务不可用</p>
            <p className="text-xs text-amber-600 mt-0.5">
              当前显示模拟数据，部分功能可能受限。请确保后端服务已启动。
            </p>
          </div>
          <button
            onClick={fetchHealth}
            className="flex items-center gap-1.5 text-xs font-medium text-amber-600 bg-amber-100 hover:bg-amber-200 px-3 py-1.5 rounded-lg transition-colors shrink-0"
          >
            <RefreshCw className="w-3 h-3" />
            重试连接
          </button>
        </div>
      )}

      {/* Analytics Cards Grid — 数据加载完成后一直展示（含降级模拟数据） */}
      {!state.loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Card 1: 名片数据总览 */}
          <AnalyticsCard
            icon={<BarChart3 className="w-5 h-5" />}
            title="名片数据总览"
            description="全局名片使用情况统计"
            gradient="bg-gradient-to-br from-blue-500 to-blue-700"
            stats={[
              { label: '名片总数', value: MOCK_DATA.cardOverview.totalCards },
              { label: '总浏览量', value: MOCK_DATA.cardOverview.totalViews },
              { label: '活跃联系人', value: MOCK_DATA.cardOverview.activeContacts },
              { label: '平均兴趣率', value: MOCK_DATA.cardOverview.avgInterestRate },
            ]}
          >
            <div className="flex items-center justify-between text-xs text-text-muted pt-3 border-t border-border-light">
              <span className="flex items-center gap-1">
                <Eye className="w-3 h-3" />
                昨日新增 +12
              </span>
              <span className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3 text-emerald-500" />
                较上周 ↑8%
              </span>
            </div>
          </AnalyticsCard>

          {/* Card 2: 人脉关系网络 */}
          <AnalyticsCard
            icon={<GitFork className="w-5 h-5" />}
            title="人脉关系网络"
            description="社交图谱与连接分析"
            gradient="bg-gradient-to-br from-emerald-500 to-emerald-700"
          >
            <NetworkOverview />
            <div className="flex items-center justify-between text-xs text-text-muted pt-3 mt-3 border-t border-border-light">
              <span className="flex items-center gap-1">
                <MessageCircle className="w-3 h-3" />
                近7日新增连接 {MOCK_DATA.network.networkGroups}
              </span>
              <button className="text-primary font-medium hover:underline">
                查看图谱 →
              </button>
            </div>
          </AnalyticsCard>

          {/* Card 3: 智能推荐 */}
          <AnalyticsCard
            icon={<Lightbulb className="w-5 h-5" />}
            title="智能推荐"
            description="AI驱动的个性化人脉推荐"
            gradient="bg-gradient-to-br from-purple-500 to-purple-700"
          >
            <RecommendationList />
          </AnalyticsCard>

          {/* Card 4: AI对话快捷入口 (新增) */}
          <AiChatQuickEntry />
        </div>
      )}

      {/* Bottom info */}
      <div className="bg-gradient-to-br from-primary/5 to-purple-500/5 rounded-2xl p-5 border border-primary/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
            <Activity className="w-5 h-5 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold text-on-surface">AI 分析报告</p>
            <p className="text-xs text-text-muted mt-0.5">
              数据每日自动更新。高级分析报告即将上线，敬请期待。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
