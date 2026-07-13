import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { CheckCircle2, HelpCircle, Sparkles, ArrowRight, Shield, CreditCard, RotateCcw, Clock } from 'lucide-react';

// ─── Types ──────────────────────────────────────────────────────────────

interface PlanFeature {
  name: string;
  description: string;
  enabled: boolean;
}

interface Plan {
  tier: string;
  name_cn: string;
  name_en: string;
  price_cents: number;
  price_yuan: string;
  interval: string;
  features: PlanFeature[];
  feature_tags: string[];
  quota_per_month: number;
  max_seats: number;
  trial_days_allowed: boolean;
  is_recommended: boolean;
}

interface TrialStatus {
  has_used_trial: boolean;
  is_active_trial: boolean;
  status: string;
  remaining_days: number;
}

interface CurrentSubscription {
  tier: string;
  status: string;
  is_trial: boolean;
}

// ─── Static fallback plans ─────────────────────────────────────────────

const FALLBACK_PLANS: Plan[] = [
  {
    tier: 'free',
    name_cn: '免费版',
    name_en: 'Free',
    price_cents: 0,
    price_yuan: '0',
    interval: 'month',
    features: [
      { name: 'AI电子名片', description: '创建并分享个人电子名片', enabled: true },
      { name: '基础匹配', description: '每日有限次匹配推荐', enabled: true },
      { name: '访客记录', description: '最近30天访客记录', enabled: true },
    ],
    feature_tags: ['AI名片', '基础匹配', '30天访客记录'],
    quota_per_month: 0,
    max_seats: 1,
    trial_days_allowed: false,
    is_recommended: false,
  },
  {
    tier: 'standard',
    name_cn: '标准版',
    name_en: 'Standard',
    price_cents: 9900,
    price_yuan: '99',
    interval: 'month',
    features: [
      { name: 'AI电子名片', description: '创建并分享个人电子名片', enabled: true },
      { name: '智能匹配', description: 'AI驱动的精准人脉匹配', enabled: true },
      { name: '无限访客记录', description: '完整访客分析', enabled: true },
      { name: '信任网络', description: '构建信任关系链', enabled: true },
      { name: '导出数据', description: '支持CSV/Excel导出', enabled: true },
      { name: 'API访问', description: '每月1000次API调用', enabled: true },
    ],
    feature_tags: ['AI名片', '智能匹配', '无限访客', '信任网络', '数据导出', 'API'],
    quota_per_month: 60,
    max_seats: 1,
    trial_days_allowed: true,
    is_recommended: true,
  },
  {
    tier: 'enterprise',
    name_cn: '企业版',
    name_en: 'Enterprise',
    price_cents: 49900,
    price_yuan: '499',
    interval: 'month',
    features: [
      { name: 'AI电子名片', description: '团队名片集中管理', enabled: true },
      { name: '智能匹配', description: 'AI驱动的精准人脉匹配', enabled: true },
      { name: '无限访客记录', description: '完整访客分析与热力图', enabled: true },
      { name: '信任网络', description: '团队级信任关系管理', enabled: true },
      { name: '导出数据', description: '支持CSV/Excel/PDF导出', enabled: true },
      { name: 'API访问', description: '每月10000次API调用', enabled: true },
      { name: 'SSO登录', description: '企业单点登录集成', enabled: true },
      { name: '自定义域名', description: '绑定企业自有域名', enabled: true },
      { name: '专属支持', description: '7×24小时专属客服', enabled: true },
      { name: '团队协作', description: '多席位团队管理', enabled: true },
    ],
    feature_tags: ['团队管理', 'SSO', '自定义域名', '专属支持', '高级API', '无限访客'],
    quota_per_month: 500,
    max_seats: 10,
    trial_days_allowed: true,
    is_recommended: false,
  },
];

// ─── Feature comparison matrix ──────────────────────────────────────────

const ALL_FEATURES: { name: string; free: boolean; standard: boolean; enterprise: boolean }[] = [
  { name: 'AI电子名片', free: true, standard: true, enterprise: true },
  { name: '基础匹配推荐', free: true, standard: true, enterprise: true },
  { name: '30天访客记录', free: true, standard: false, enterprise: false },
  { name: 'AI智能匹配', free: false, standard: true, enterprise: true },
  { name: '无限访客分析', free: false, standard: true, enterprise: true },
  { name: '信任网络', free: false, standard: true, enterprise: true },
  { name: '数据导出 (CSV/Excel)', free: false, standard: true, enterprise: true },
  { name: 'API访问', free: false, standard: true, enterprise: true },
  { name: '数据导出 (PDF)', free: false, standard: false, enterprise: true },
  { name: 'SSO企业登录', free: false, standard: false, enterprise: true },
  { name: '自定义域名', free: false, standard: false, enterprise: true },
  { name: '专属客服 7×24h', free: false, standard: false, enterprise: true },
  { name: '团队协作管理', free: false, standard: false, enterprise: true },
  { name: '多席位支持', free: false, standard: false, enterprise: true },
];

// ─── Helpers ────────────────────────────────────────────────────────────

function formatPrice(cents: number): string {
  if (cents === 0) return '免费';
  return `¥${(cents / 100).toFixed(0)}`;
}

// ─── PricingCard Component ─────────────────────────────────────────────

function PricingCard({
  plan,
  currentTier,
  trialStatus,
  onSelectPlan,
  onStartTrial,
  loading,
}: {
  plan: Plan;
  currentTier: string;
  trialStatus: TrialStatus | null;
  onSelectPlan: (tier: string) => void;
  onStartTrial: () => void;
  loading: boolean;
}) {
  const isFree = plan.tier === 'free';
  const isCurrent = currentTier === plan.tier;
  const canTrial = plan.trial_days_allowed && !trialStatus?.has_used_trial && !trialStatus?.is_active_trial;

  return (
    <div
      className={`
        relative flex flex-col rounded-2xl border transition-all duration-300
        ${plan.is_recommended
          ? 'border-sky-400 shadow-modal shadow-sky-200/50 dark:shadow-sky-900/30 scale-[1.02] z-10'
          : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 shadow-card hover:shadow-elevated'
        }
        bg-white dark:bg-dark-surface
      `}
    >
      {/* Recommended badge */}
      {plan.is_recommended && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <span className="inline-flex items-center gap-1.5 bg-gradient-to-r from-sky-500 to-blue-600 text-white text-xs font-semibold px-4 py-1.5 rounded-full shadow-elevated">
            <Sparkles className="w-3.5 h-3.5" />
            最受欢迎
          </span>
        </div>
      )}

      {/* Trial badge */}
      {canTrial && (
        <div className="absolute -top-4 right-4">
          <span className="inline-flex items-center gap-1 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 text-xs font-semibold px-3 py-1 rounded-full border border-emerald-200 dark:border-emerald-700">
            <Clock className="w-3 h-3" />
            可试用
          </span>
        </div>
      )}

      {/* Header */}
      <div className={`p-6 pb-0 ${plan.is_recommended ? 'pt-8' : ''}`}>
        <h3 className="text-lg font-bold text-slate-900 dark:text-dark-text">
          {plan.name_cn}
        </h3>
        <p className="text-sm text-slate-500 dark:text-dark-muted mt-0.5">
          {plan.name_en}
        </p>

        {/* Price */}
        <div className="mt-4 flex items-baseline gap-1">
          <span className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-dark-text">
            {isFree ? '免费' : `¥${plan.price_yuan}`}
          </span>
          {!isFree && (
            <span className="text-sm text-slate-500 dark:text-dark-muted">/月</span>
          )}
        </div>

        {/* Description */}
        <p className="mt-2 text-sm text-slate-500 dark:text-dark-muted leading-relaxed">
          {plan.tier === 'free' && '基础功能，适合个人体验'}
          {plan.tier === 'standard' && '解锁AI智能匹配与完整数据分析'}
          {plan.tier === 'enterprise' && '团队协作与企业级定制解决方案'}
        </p>

        {/* Feature tags */}
        <div className="mt-4 flex flex-wrap gap-1.5">
          {plan.feature_tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="inline-block text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
            >
              {tag}
            </span>
          ))}
          {plan.feature_tags.length > 4 && (
            <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-400">
              +{plan.feature_tags.length - 4}
            </span>
          )}
        </div>
      </div>

      {/* Features list */}
      <div className="flex-1 px-6 py-5">
        <ul className="space-y-2.5">
          {plan.features.map((feat) => (
            <li key={feat.name} className="flex items-start gap-2.5 text-sm">
              <CheckCircle2 className="w-4 h-4 mt-0.5 text-emerald-500 shrink-0" />
              <span className="text-slate-700 dark:text-slate-300">
                {feat.description}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* CTA */}
      <div className="p-6 pt-0 space-y-2">
        {isFree ? (
          <button
            disabled
            className="w-full py-2.5 rounded-xl text-sm font-semibold bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 cursor-not-allowed"
          >
            当前使用中
          </button>
        ) : isCurrent ? (
          <button
            disabled
            className="w-full py-2.5 rounded-xl text-sm font-semibold bg-sky-50 dark:bg-sky-900/20 text-sky-600 dark:text-sky-400 cursor-not-allowed border border-sky-200 dark:border-sky-800"
          >
            当前订阅
          </button>
        ) : (
          <>
            <button
              onClick={() => onSelectPlan(plan.tier)}
              disabled={loading}
              className={`
                w-full py-2.5 rounded-xl text-sm font-semibold transition-all duration-200
                ${plan.is_recommended
                  ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-elevated hover:shadow-elevated hover:from-sky-600 hover:to-blue-700 active:scale-[0.98]'
                  : 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-slate-100 active:scale-[0.98]'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              {loading ? '处理中...' : `升级至${plan.name_cn}`}
            </button>

            {/* Trial CTA for standard */}
            {canTrial && plan.tier === 'standard' && (
              <button
                onClick={onStartTrial}
                disabled={loading}
                className="w-full py-2.5 rounded-xl text-sm font-semibold border-2 border-emerald-500 text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-all duration-200 active:scale-[0.98] disabled:opacity-50"
              >
                🎉 14天免费试用
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ─── FAQ Accordion ──────────────────────────────────────────────────────

const FAQS = [
  {
    q: '免费版和付费版有什么区别？',
    a: '免费版提供基础的名片创建和有限匹配推荐。标准版解锁AI智能匹配、无限访客分析和API访问。企业版额外包含团队管理、SSO登录、自定义域名和专属客服支持。',
  },
  {
    q: '14天免费试用需要绑定支付方式吗？',
    a: '不需要。您可以直接开始试用标准版全部功能，14天内随时取消，无需绑定任何支付方式。试用到期后自动降级为免费版。',
  },
  {
    q: '我可以在套餐之间升降级吗？',
    a: '可以。您可以在免费版、标准版和企业版之间自由升级。降级操作在当前计费周期结束后生效，确保您已付费的服务不受影响。',
  },
  {
    q: '企业版支持多少人使用？',
    a: '企业版支持最多10个席位，适合团队协作。每个成员都可以拥有自己的AI名片，共享访客分析和信任网络。如需更多席位，请联系我们的销售团队。',
  },
  {
    q: '支付安全吗？支持哪些方式？',
    a: '我们支持微信支付和支付宝，所有支付通过加密通道进行，保障您的资金安全。我们还会为每位付费用户开具正式发票。',
  },
];

// ─── Main Component ────────────────────────────────────────────────────

export default function PricingPage() {
  const navigate = useNavigate();
  const [plans, setPlans] = useState<Plan[]>(FALLBACK_PLANS);
  const [currentTier, setCurrentTier] = useState<string>('free');
  const [trialStatus, setTrialStatus] = useState<TrialStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [showCompare, setShowCompare] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError('');

    try {
      // Load plans
      const plansRes = await api.get<Plan[]>('/api/subscription/plans');
      if (plansRes.code === 200 && plansRes.data) {
        setPlans(plansRes.data);
      }

      // Load current subscription
      const subRes = await api.get<CurrentSubscription>('/api/subscription/current');
      if (subRes.code === 200 && subRes.data) {
        setCurrentTier(subRes.data.tier);
      }

      // Load trial status
      const trialRes = await api.get<TrialStatus>('/api/subscription/trial/status');
      if (trialRes.code === 200 && trialRes.data) {
        setTrialStatus(trialRes.data);
      }
    } catch (e: any) {
      // Silently use fallback data
      console.warn('Failed to load pricing data, using fallback:', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectPlan(tier: string) {
    setActionLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      const res = await api.post('/api/subscription/upgrade', {
        target_tier: tier,
        company_name: '',
        seats: 1,
      });

      if (res.code === 200) {
        setSuccessMsg(`🎉 成功升级至${plans.find(p => p.tier === tier)?.name_cn || ''}！`);
        setCurrentTier(tier);
        setTimeout(() => setSuccessMsg(''), 4000);
      } else {
        setError(res.message || '升级失败');
      }
    } catch (e: any) {
      setError(e.message || '网络错误，请重试');
    } finally {
      setActionLoading(false);
    }
  }

  async function handleStartTrial() {
    setActionLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      const res = await api.post('/api/subscription/trial/start', {
        company_name: '',
      });

      if (res.code === 200) {
        setSuccessMsg('🎉 恭喜！您已成功开通14天免费试用（标准版），尽情体验全部功能！');
        setCurrentTier('standard');
        setTrialStatus({
          has_used_trial: true,
          is_active_trial: true,
          status: 'trial',
          remaining_days: 14,
        });
        setTimeout(() => setSuccessMsg(''), 5000);
      } else {
        setError(res.message || '开通试用失败');
      }
    } catch (e: any) {
      setError(e.message || '网络错误，请重试');
    } finally {
      setActionLoading(false);
    }
  }

  // ── Loading state ──
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-dark-bg py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16 animate-pulse">
            <div className="h-10 w-64 bg-slate-200 dark:bg-slate-700 rounded-lg mx-auto mb-4" />
            <div className="h-5 w-96 bg-slate-200 dark:bg-slate-700 rounded mx-auto" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
            {[1, 2, 3].map((i) => (
              <div key={i} className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-dark-surface p-6 animate-pulse">
                <div className="h-6 w-20 bg-slate-200 dark:bg-slate-700 rounded mb-3" />
                <div className="h-4 w-16 bg-slate-200 dark:bg-slate-700 rounded mb-4" />
                <div className="h-12 w-32 bg-slate-200 dark:bg-slate-700 rounded mb-6" />
                <div className="space-y-3">
                  {[1, 2, 3, 4, 5].map((j) => (
                    <div key={j} className="h-4 bg-slate-200 dark:bg-slate-700 rounded" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Sort plans: free, standard, enterprise
  const sortedPlans = [...plans].sort((a, b) => {
    const order = { free: 0, standard: 1, enterprise: 2 };
    return (order[a.tier as keyof typeof order] ?? 99) - (order[b.tier as keyof typeof order] ?? 99);
  });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-dark-bg">
      {/* ── Hero ‑─────────────────────────────────────────── */}
      <div className="relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-sky-100 dark:bg-sky-900/20 opacity-60 blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-blue-100 dark:bg-blue-900/20 opacity-60 blur-3xl" />
        </div>

        <div className="relative pt-16 pb-8 md:pt-24 md:pb-12 px-4">
          <div className="max-w-6xl mx-auto text-center">
            {/* Trial CTA banner */}
            {(!trialStatus?.has_used_trial && !trialStatus?.is_active_trial) && (
              <div className="inline-flex items-center gap-2 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border border-emerald-200 dark:border-emerald-700 rounded-full px-4 py-1.5 mb-6">
                <Sparkles className="w-4 h-4 text-emerald-500" />
                <span className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
                  新用户可享 <strong>14天免费试用</strong> 标准版
                </span>
              </div>
            )}

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-dark-text">
              选择最适合您的
              <span className="block mt-1 bg-gradient-to-r from-sky-500 to-blue-600 bg-clip-text text-transparent">
                套餐方案
              </span>
            </h1>
            <p className="mt-4 text-lg text-slate-500 dark:text-dark-muted max-w-2xl mx-auto leading-relaxed">
              从个人到企业，找到属于您的AI数字名片解决方案。
              所有付费套餐均享受 <strong className="text-slate-700 dark:text-slate-300">14天无理由退款</strong> 保障。
            </p>

            {/* Active trial indicator */}
            {trialStatus?.is_active_trial && (
              <div className="mt-6 inline-flex items-center gap-2 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700 rounded-lg px-5 py-2.5">
                <Clock className="w-5 h-5 text-emerald-500" />
                <span className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
                  试用中 · 剩余 <strong>{trialStatus.remaining_days}天</strong>
                </span>
              </div>
            )}

            {/* Active subscription indicator */}
            {currentTier !== 'free' && !trialStatus?.is_active_trial && (
              <div className="mt-6 inline-flex items-center gap-2 bg-sky-50 dark:bg-sky-900/20 border border-sky-200 dark:border-sky-700 rounded-lg px-5 py-2.5">
                <CheckCircle2 className="w-5 h-5 text-sky-500" />
                <span className="text-sm font-medium text-sky-700 dark:text-sky-300">
                  当前订阅：{plans.find(p => p.tier === currentTier)?.name_cn || currentTier}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Messages ─────────────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-4">
        {successMsg && (
          <div className="mb-6 p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700 rounded-xl text-emerald-700 dark:text-emerald-300 text-sm text-center font-medium animate-fadeIn">
            {successMsg}
          </div>
        )}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-xl text-red-700 dark:text-red-300 text-sm text-center">
            {error}
          </div>
        )}
      </div>

      {/* ── Pricing Cards ────────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-4 pb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8 items-start">
          {sortedPlans.map((plan) => (
            <PricingCard
              key={plan.tier}
              plan={plan}
              currentTier={currentTier}
              trialStatus={trialStatus}
              onSelectPlan={handleSelectPlan}
              onStartTrial={handleStartTrial}
              loading={actionLoading}
            />
          ))}
        </div>

        {/* ── Guarantee strip ──────────────────────────────── */}
        <div className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { icon: CreditCard, text: '微信 / 支付宝支付' },
            { icon: Shield, text: '加密安全支付' },
            { icon: RotateCcw, text: '14天无理由退款' },
            { icon: CheckCircle2, text: '正规发票' },
          ].map((item) => (
            <div
              key={item.text}
              className="flex items-center gap-2.5 justify-center p-3 rounded-xl bg-white dark:bg-dark-surface border border-slate-200 dark:border-slate-700 text-sm text-slate-600 dark:text-slate-400"
            >
              <item.icon className="w-4 h-4 text-sky-500 shrink-0" />
              <span>{item.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Feature Comparison Table ──────────────────────── */}
      <div className="max-w-5xl mx-auto px-4 pb-8">
        <div className="text-center mb-8">
          <button
            onClick={() => setShowCompare(!showCompare)}
            className="inline-flex items-center gap-2 text-sm font-medium text-sky-600 dark:text-sky-400 hover:text-sky-700 dark:hover:text-sky-300 transition-colors"
          >
            <span>{showCompare ? '收起' : '查看'}完整功能对比</span>
            <svg
              className={`w-4 h-4 transition-transform ${showCompare ? 'rotate-180' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        {showCompare && (
          <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-dark-surface shadow-card">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left px-5 py-4 font-semibold text-slate-900 dark:text-dark-text">功能</th>
                  <th className="text-center px-5 py-4 font-semibold text-slate-900 dark:text-dark-text w-28">免费版</th>
                  <th className="text-center px-5 py-4 font-semibold text-sky-600 dark:text-sky-400 w-28 bg-sky-50/50 dark:bg-sky-900/10">标准版</th>
                  <th className="text-center px-5 py-4 font-semibold text-slate-900 dark:text-dark-text w-28">企业版</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                {ALL_FEATURES.map((feat) => (
                  <tr key={feat.name} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="px-5 py-3.5 text-slate-700 dark:text-slate-300">{feat.name}</td>
                    <td className="text-center px-5 py-3.5">
                      {feat.free ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 mx-auto" />
                      ) : (
                        <span className="text-slate-300 dark:text-slate-600">—</span>
                      )}
                    </td>
                    <td className="text-center px-5 py-3.5 bg-sky-50/30 dark:bg-sky-900/5">
                      {feat.standard ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 mx-auto" />
                      ) : (
                        <span className="text-slate-300 dark:text-slate-600">—</span>
                      )}
                    </td>
                    <td className="text-center px-5 py-3.5">
                      {feat.enterprise ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 mx-auto" />
                      ) : (
                        <span className="text-slate-300 dark:text-slate-600">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── FAQ ────────────────────────────────────────────── */}
      <div className="max-w-3xl mx-auto px-4 pb-16">
        <h2 className="text-2xl font-bold text-center text-slate-900 dark:text-dark-text mb-8">
          常见问题
        </h2>
        <div className="space-y-3">
          {FAQS.map((faq, i) => (
            <div
              key={i}
              className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-dark-surface overflow-hidden transition-all duration-200"
            >
              <button
                className="w-full flex items-center justify-between px-5 py-4 text-left"
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
              >
                <span className="font-medium text-slate-900 dark:text-dark-text text-sm">{faq.q}</span>
                <HelpCircle className={`w-4 h-4 text-slate-400 transition-transform ${openFaq === i ? 'rotate-180' : ''}`} />
              </button>
              {openFaq === i && (
                <div className="px-5 pb-4 text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-10 text-center">
          <p className="text-sm text-slate-500 dark:text-dark-muted mb-4">
            还有疑问？我们的团队随时为您解答
          </p>
          <div className="flex items-center justify-center gap-4">
            <a
              href="mailto:support@ainamecard.com"
              className="inline-flex items-center gap-2 text-sm font-medium text-sky-600 dark:text-sky-400 hover:text-sky-700 dark:hover:text-sky-300 transition-colors"
            >
              联系客服 <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
