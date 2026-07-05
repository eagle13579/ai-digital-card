import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import {
  CheckCircle2, HelpCircle, Sparkles, ArrowRight, Shield, CreditCard,
  RotateCcw, Clock, Flame, Zap, Users, Gem, Building2, Microscope,
  Download, Server, FileText, BarChart3, Globe, BookOpen,
} from 'lucide-react';

// ─── Types ──────────────────────────────────────────────────────────────

interface PlanMECE {
  tier: string;           // free | pro | enterprise | group
  category: string;       // 引流 | 粘性 | 利润
  name_cn: string;
  name_en: string;
  price_monthly: number;  // 月付价格（元）
  price_yearly: number;   // 年付价格（元，月均）
  interval: string;
  features: { name: string; enabled: boolean; highlight?: boolean }[];
  is_recommended: boolean;
  badge_text?: string;
  cta_text: string;
  cta_variant: 'default' | 'primary' | 'outline';
  max_seats: number;
  quota_cards: number;
  quota_ocr: number;
  quota_visitors: number;
}

interface PricingData {
  plans: PlanMECE[];
  api_pricing: ApiPricingItem[];
  enterprise_addons: EnterpriseAddon[];
  faqs: FaqItem[];
}

interface ApiPricingItem {
  name: string;
  unit: string;
  price: string; // e.g. "¥0.1/次"
}

interface EnterpriseAddon {
  name: string;
  price: string;
  description: string;
  icon: string;
}

interface FaqItem {
  q: string;
  a: string;
}

// ─── Static MECE Plans (fallback + main data) ───────────────────────────

const MECE_PLANS: PlanMECE[] = [
  // 引流层 — 免费
  {
    tier: 'free',
    category: '引流',
    name_cn: '免费版',
    name_en: 'Free',
    price_monthly: 0,
    price_yearly: 0,
    interval: 'month',
    features: [
      { name: '1张AI电子名片', enabled: true },
      { name: '3次OCR识别/月', enabled: true },
      { name: '5位访客记录', enabled: true },
      { name: '基础个人主页', enabled: true },
      { name: 'AI智能匹配', enabled: false },
      { name: '访客实时追踪', enabled: false },
      { name: '数据分析看板', enabled: false },
    ],
    is_recommended: false,
    cta_text: '当前使用中',
    cta_variant: 'default',
    max_seats: 1,
    quota_cards: 1,
    quota_ocr: 3,
    quota_visitors: 5,
  },
  // 粘性层 — Pro（重点突出）
  {
    tier: 'pro',
    category: '粘性',
    name_cn: 'Pro',
    name_en: 'Professional',
    price_monthly: 19.9,
    price_yearly: 199,   // 199/年 ≈ 16.58/月
    interval: 'month',
    features: [
      { name: '无限AI电子名片', enabled: true, highlight: true },
      { name: '无限OCR识别', enabled: true, highlight: true },
      { name: '无限访客追踪', enabled: true, highlight: true },
      { name: 'AI智能匹配推荐', enabled: true },
      { name: '访客实时通知', enabled: true },
      { name: '数据分析看板', enabled: true, highlight: true },
      { name: '名片分组管理', enabled: true },
      { name: '数据导出(CSV/Excel)', enabled: true },
    ],
    is_recommended: true,
    badge_text: '最受欢迎',
    cta_text: '升级至Pro',
    cta_variant: 'primary',
    max_seats: 1,
    quota_cards: 999999,
    quota_ocr: 999999,
    quota_visitors: 999999,
  },
  // 利润层 — Enterprise
  {
    tier: 'enterprise',
    category: '利润',
    name_cn: '企业版',
    name_en: 'Enterprise',
    price_monthly: 199,
    price_yearly: 1990,  // 1990/年 ≈ 165.8/月
    interval: 'month',
    features: [
      { name: '50人团队协作', enabled: true, highlight: true },
      { name: 'SSO单点登录', enabled: true },
      { name: '批量名片导入', enabled: true, highlight: true },
      { name: '团队权限管理', enabled: true },
      { name: '自定义域名', enabled: true },
      { name: '企业访客看板', enabled: true },
      { name: '专属客服 7×24h', enabled: true },
      { name: 'API高级访问', enabled: true },
    ],
    is_recommended: false,
    cta_text: '联系销售',
    cta_variant: 'outline',
    max_seats: 50,
    quota_cards: 999999,
    quota_ocr: 999999,
    quota_visitors: 999999,
  },
  // 利润层 — Group
  {
    tier: 'group',
    category: '利润',
    name_cn: '集团版',
    name_en: 'Group',
    price_monthly: 299,
    price_yearly: 2990,  // 2990/年 ≈ 249/月
    interval: 'month',
    features: [
      { name: '200人团队协作', enabled: true, highlight: true },
      { name: '定制匹配引擎', enabled: true, highlight: true },
      { name: '私有化部署选项', enabled: true },
      { name: '高级SSO + AD/LDAP', enabled: true },
      { name: '专属客户成功经理', enabled: true, highlight: true },
      { name: 'SLA保障 99.9%', enabled: true },
      { name: '无限API调用', enabled: true },
      { name: '定制开发支持', enabled: true },
    ],
    is_recommended: false,
    cta_text: '联系销售',
    cta_variant: 'outline',
    max_seats: 200,
    quota_cards: 999999,
    quota_ocr: 999999,
    quota_visitors: 999999,
  },
];

const API_PRICING: ApiPricingItem[] = [
  { name: 'OCR名片识别', unit: '次', price: '¥0.10/次' },
  { name: '人脉智能匹配', unit: '次', price: '¥0.05/次' },
  { name: '关系图谱构建', unit: '次', price: '¥0.20/次' },
  { name: '名片信息查询', unit: '次', price: '¥0.02/次' },
];

const ENTERPRISE_ADDONS: EnterpriseAddon[] = [
  { name: '企业电子画册', price: '¥999/年', description: '企业专属电子画册制作与发布', icon: 'BookOpen' },
  { name: '合规审计套件', price: '¥9,999/年', description: 'GDPR/等保合规审计与报告', icon: 'Shield' },
  { name: '私有化部署', price: '¥99,999起', description: '全栈私有化部署，数据自主可控', icon: 'Server' },
];

const FAQS: FaqItem[] = [
  { q: '免费版和Pro版有什么区别？', a: '免费版提供1张名片、每月3次OCR识别和5位访客记录，适合个人初步体验。Pro版解锁无限名片、无限OCR识别、无限访客追踪以及AI智能匹配分析，是个人用户的最佳选择。' },
  { q: '年付比月付划算多少？', a: 'Pro版年付仅需¥199/年（月均约¥16.6），相比月付¥19.9×12=¥238.8节省近17%。企业版年付¥1,990/年（月均约¥166），相比月付¥199×12=¥2,388节省约17%。集团版同理。' },
  { q: '企业版和集团版如何选择？', a: '50人以内团队推荐企业版（¥199/月），支持SSO、批量名片导入和自定义域名。200人以内或需要定制匹配引擎、私有化部署的客户推荐集团版（¥299/月）。两个版本均可联系销售获取专属方案。' },
  { q: 'API按量付费如何计费？', a: 'API按实际调用量计费，月度结算。OCR名片识别¥0.10/次，人脉智能匹配¥0.05/次，关系图谱构建¥0.20/次。企业版和集团版用户可享受额外折扣。' },
  { q: '支付安全吗？支持哪些方式？', a: '我们支持微信支付和支付宝，所有支付通过加密通道进行。支持开具正规发票，14天内无理由退款。' },
];

// ─── Icon resolver ──────────────────────────────────────────────────────

function resolveAddonIcon(name: string) {
  switch (name) {
    case 'BookOpen': return BookOpen;
    case 'Shield': return Shield;
    case 'Server': return Server;
    default: return Gem;
  }
}

// ─── Helpers ────────────────────────────────────────────────────────────

function formatPrice(price: number, showFree = true): string {
  if (price === 0 && showFree) return '免费';
  if (Number.isInteger(price)) return `¥${price}`;
  return `¥${price.toFixed(1)}`;
}

// ─── Sub-components ─────────────────────────────────────────────────────

function CategoryBadge({ category }: { category: string }) {
  const colors: Record<string, string> = {
    '引流': 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-700',
    '粘性': 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-700',
    '利润': 'bg-violet-50 dark:bg-violet-900/20 text-violet-600 dark:text-violet-400 border-violet-200 dark:border-violet-700',
  };
  const icons: Record<string, React.ElementType> = {
    '引流': Users,
    '粘性': Flame,
    '利润': Gem,
  };
  const Icon = icons[category] || Sparkles;
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${colors[category] || ''}`}>
      <Icon className="w-3 h-3" />
      {category}
    </span>
  );
}

function PricingCard({
  plan,
  isYearly,
  currentTier,
  onAction,
  actionLoading,
}: {
  plan: PlanMECE;
  isYearly: boolean;
  currentTier: string;
  onAction: (tier: string) => void;
  actionLoading: boolean;
}) {
  const isFree = plan.tier === 'free';
  const isCurrent = currentTier === plan.tier;
  const displayPrice = isYearly ? plan.price_yearly : plan.price_monthly;

  return (
    <div
      className={`
        relative flex flex-col rounded-2xl border transition-all duration-300
        ${plan.is_recommended
          ? 'border-amber-400 shadow-xl shadow-amber-200/40 dark:shadow-amber-900/30 scale-[1.03] z-10 ring-1 ring-amber-300 dark:ring-amber-600'
          : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 shadow-sm hover:shadow-md'
        }
        bg-white dark:bg-dark-surface
      `}
    >
      {/* Recommended badge */}
      {plan.is_recommended && plan.badge_text && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-20">
          <span className="inline-flex items-center gap-1.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs font-bold px-4 py-1.5 rounded-full shadow-lg">
            <Flame className="w-3.5 h-3.5" />
            {plan.badge_text}
          </span>
        </div>
      )}

      {/* Header */}
      <div className={`p-6 pb-0 ${plan.is_recommended ? 'pt-8' : ''}`}>
        {/* Category + plan name row */}
        <div className="flex items-center justify-between mb-1">
          <CategoryBadge category={plan.category} />
        </div>
        <div className="flex items-baseline gap-2 mt-2">
          <h3 className="text-xl font-bold text-slate-900 dark:text-dark-text">
            {plan.name_cn}
          </h3>
          <span className="text-xs text-slate-400 dark:text-dark-muted">
            {plan.name_en}
          </span>
        </div>

        {/* Price */}
        <div className="mt-4 flex items-baseline gap-1">
          <span className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-dark-text">
            {isFree ? '免费' : formatPrice(displayPrice)}
          </span>
          {!isFree && (
            <span className="text-sm text-slate-500 dark:text-dark-muted">
              {isYearly ? '/年' : '/月'}
            </span>
          )}
        </div>
        {!isFree && isYearly && (
          <p className="mt-1 text-xs text-slate-400 dark:text-dark-muted">
            月均 {formatPrice(plan.price_yearly / 12)} · 省 {Math.round((1 - plan.price_yearly / (plan.price_monthly * 12)) * 100)}%
          </p>
        )}
        {!isFree && !isYearly && (
          <p className="mt-1 text-xs text-slate-400 dark:text-dark-muted">
            年付仅 {formatPrice(plan.price_yearly)} · 省 {Math.round((1 - plan.price_yearly / (plan.price_monthly * 12)) * 100)}%
          </p>
        )}

        {/* Mini quota badges */}
        <div className="mt-4 flex flex-wrap gap-1.5">
          <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-sky-50 dark:bg-sky-900/20 text-sky-600 dark:text-sky-400 border border-sky-200 dark:border-sky-700">
            <FileText className="w-3 h-3" />
            {plan.quota_cards >= 999999 ? '无限' : plan.quota_cards}名片
          </span>
          <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-violet-50 dark:bg-violet-900/20 text-violet-600 dark:text-violet-400 border border-violet-200 dark:border-violet-700">
            <Microscope className="w-3 h-3" />
            {plan.quota_ocr >= 999999 ? '无限' : plan.quota_ocr}次OCR
          </span>
          <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-700">
            <BarChart3 className="w-3 h-3" />
            {plan.quota_visitors >= 999999 ? '无限' : plan.quota_visitors}访客
          </span>
        </div>
      </div>

      {/* Features list */}
      <div className="flex-1 px-6 py-5">
        <ul className="space-y-2.5">
          {plan.features.map((feat) => (
            <li key={feat.name} className="flex items-start gap-2.5 text-sm">
              {feat.enabled ? (
                <CheckCircle2 className={`w-4 h-4 mt-0.5 shrink-0 ${feat.highlight ? 'text-amber-500' : 'text-emerald-500'}`} />
              ) : (
                <span className="w-4 h-4 mt-0.5 shrink-0 text-slate-300 dark:text-slate-600">—</span>
              )}
              <span className={`${feat.enabled ? 'text-slate-700 dark:text-slate-300' : 'text-slate-400 dark:text-slate-500'} ${feat.highlight ? 'font-semibold' : ''}`}>
                {feat.name}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* CTA */}
      <div className="p-6 pt-0">
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
        ) : plan.cta_variant === 'primary' ? (
          <button
            onClick={() => onAction(plan.tier)}
            disabled={actionLoading}
            className="w-full py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-md hover:shadow-lg hover:from-amber-600 hover:to-orange-600 active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLoading ? '处理中...' : plan.cta_text}
          </button>
        ) : plan.cta_variant === 'outline' ? (
          <button
            onClick={() => onAction(plan.tier)}
            disabled={actionLoading}
            className="w-full py-2.5 rounded-xl text-sm font-semibold border-2 border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 bg-white dark:bg-dark-surface hover:bg-slate-50 dark:hover:bg-slate-800 active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLoading ? '处理中...' : plan.cta_text}
          </button>
        ) : (
          <button
            onClick={() => onAction(plan.tier)}
            disabled={actionLoading}
            className="w-full py-2.5 rounded-xl text-sm font-semibold bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-slate-100 active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLoading ? '处理中...' : plan.cta_text}
          </button>
        )}
      </div>
    </div>
  );
}

function ApiPricingTable({ items }: { items: ApiPricingItem[] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-dark-surface shadow-sm">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
            <th className="text-left px-5 py-3 font-semibold text-slate-900 dark:text-dark-text">服务项目</th>
            <th className="text-center px-5 py-3 font-semibold text-slate-900 dark:text-dark-text">计费单位</th>
            <th className="text-right px-5 py-3 font-semibold text-slate-900 dark:text-dark-text">价格</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
          {items.map((item) => (
            <tr key={item.name} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
              <td className="px-5 py-3.5 text-slate-700 dark:text-slate-300 font-medium">{item.name}</td>
              <td className="px-5 py-3.5 text-center text-slate-500 dark:text-dark-muted">{item.unit}</td>
              <td className="px-5 py-3.5 text-right text-sky-600 dark:text-sky-400 font-semibold">{item.price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AddonCard({ addon }: { addon: EnterpriseAddon }) {
  const Icon = resolveAddonIcon(addon.icon);
  return (
    <div className="flex flex-col p-5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-dark-surface hover:shadow-md transition-all duration-200 hover:border-slate-300 dark:hover:border-slate-600">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-50 to-indigo-50 dark:from-violet-900/20 dark:to-indigo-900/20 flex items-center justify-center border border-violet-200 dark:border-violet-700">
          <Icon className="w-5 h-5 text-violet-600 dark:text-violet-400" />
        </div>
        <div>
          <h4 className="font-semibold text-slate-900 dark:text-dark-text text-sm">{addon.name}</h4>
          <p className="text-xs text-slate-500 dark:text-dark-muted">{addon.description}</p>
        </div>
      </div>
      <div className="mt-auto flex items-center justify-between">
        <span className="text-lg font-bold text-slate-900 dark:text-dark-text">{addon.price}</span>
        <button className="text-xs font-medium text-sky-600 dark:text-sky-400 hover:text-sky-700 dark:hover:text-sky-300 transition-colors">
          了解详情 →
        </button>
      </div>
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────

export default function PricingPage() {
  const navigate = useNavigate();
  const [isYearly, setIsYearly] = useState(false);
  const [currentTier, setCurrentTier] = useState<string>('free');
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPricing();
  }, []);

  async function loadPricing() {
    setLoading(true);
    try {
      // Fetch pricing from backend
      const res = await api.get<any>('/api/v1/membership/pricing');
      if (res.code === 200 && res.data) {
        // Backend data used if available; fallback to static data
        console.log('Pricing data loaded:', res.data);
      }
      // Also fetch current subscription tier
      const subRes = await api.get<any>('/api/subscription/current');
      if (subRes.code === 200 && subRes.data?.tier) {
        setCurrentTier(subRes.data.tier);
      }
    } catch (e: any) {
      console.warn('Failed to load pricing data, using fallback:', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpgrade(tier: string) {
    // For enterprise/group, navigate to contact sales
    if (tier === 'enterprise' || tier === 'group') {
      navigate('/contact-sales');
      return;
    }

    setActionLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      const res = await api.post('/api/subscription/upgrade', {
        target_tier: tier,
        interval: isYearly ? 'year' : 'month',
      });

      if (res.code === 200) {
        const planName = MECE_PLANS.find(p => p.tier === tier)?.name_cn || tier;
        setSuccessMsg(`🎉 成功升级至${planName}！`);
        setCurrentTier(tier);
        setTimeout(() => setSuccessMsg(''), 4000);
      } else {
        setError(res.message || '升级失败，请重试');
      }
    } catch (e: any) {
      setError(e.message || '网络错误，请检查连接');
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
            <div className="h-5 w-96 bg-slate-200 dark:bg-slate-700 rounded mx-auto mb-6" />
            <div className="flex justify-center gap-2">
              <div className="h-8 w-32 bg-slate-200 dark:bg-slate-700 rounded-full" />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-dark-surface p-6 animate-pulse">
                <div className="h-5 w-16 bg-slate-200 dark:bg-slate-700 rounded mb-3" />
                <div className="h-10 w-28 bg-slate-200 dark:bg-slate-700 rounded mb-6" />
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

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-dark-bg">
      {/* ── Hero ──────────────────────────────────────────────── */}
      <div className="relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-amber-100 dark:bg-amber-900/20 opacity-40 blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-sky-100 dark:bg-sky-900/20 opacity-40 blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-violet-100 dark:bg-violet-900/10 opacity-30 blur-3xl" />
        </div>

        <div className="relative pt-16 pb-8 md:pt-24 md:pb-12 px-4">
          <div className="max-w-6xl mx-auto text-center">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-dark-text">
              简单透明的
              <span className="block mt-1 bg-gradient-to-r from-amber-500 via-orange-500 to-sky-600 bg-clip-text text-transparent">
                三层定价
              </span>
            </h1>
            <p className="mt-4 text-lg text-slate-500 dark:text-dark-muted max-w-2xl mx-auto leading-relaxed">
              引流 · 粘性 · 利润 —— 从个人免费体验到集团级部署，找到最适合您的方案。
              所有付费套餐均享受 <strong className="text-slate-700 dark:text-slate-300">14天无理由退款</strong> 保障。
            </p>

            {/* Monthly / Yearly toggle */}
            <div className="mt-8 inline-flex items-center gap-3 p-1 rounded-full bg-white dark:bg-dark-surface border border-slate-200 dark:border-slate-700 shadow-sm">
              <button
                onClick={() => setIsYearly(false)}
                className={`px-5 py-2 rounded-full text-sm font-semibold transition-all duration-200 ${
                  !isYearly
                    ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-sm'
                    : 'text-slate-500 dark:text-dark-muted hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                月付
              </button>
              <button
                onClick={() => setIsYearly(true)}
                className={`px-5 py-2 rounded-full text-sm font-semibold transition-all duration-200 inline-flex items-center gap-1.5 ${
                  isYearly
                    ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-sm'
                    : 'text-slate-500 dark:text-dark-muted hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                年付
                <span className="text-[10px] bg-emerald-400 text-white px-1.5 py-0.5 rounded-full font-bold">省17%</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Messages ─────────────────────────────────────────── */}
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

      {/* ── MECE Three-Layer Pricing Cards ──────────────────── */}
      <div className="max-w-6xl mx-auto px-4 pb-8">
        {/* Layer labels */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-4">
          {MECE_PLANS.map((plan) => (
            <div key={plan.tier} className="text-center">
              <span className={`inline-flex items-center gap-1.5 text-xs font-bold tracking-wider uppercase px-3 py-1 rounded-full border ${
                plan.category === '引流'
                  ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-700'
                  : plan.category === '粘性'
                  ? 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-700'
                  : 'bg-violet-50 dark:bg-violet-900/20 text-violet-600 dark:text-violet-400 border-violet-200 dark:border-violet-700'
              }`}>
                {plan.category === '引流' && <Users className="w-3 h-3" />}
                {plan.category === '粘性' && <Flame className="w-3 h-3" />}
                {plan.category === '利润' && <Gem className="w-3 h-3" />}
                {plan.category}层·{plan.name_cn}
              </span>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-start">
          {MECE_PLANS.map((plan) => (
            <PricingCard
              key={plan.tier}
              plan={plan}
              isYearly={isYearly}
              currentTier={currentTier}
              onAction={handleUpgrade}
              actionLoading={actionLoading}
            />
          ))}
        </div>

        {/* Guarantee strip */}
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

      {/* ── API Pricing Table ────────────────────────────────── */}
      <div className="bg-white dark:bg-dark-surface border-t border-b border-slate-200 dark:border-slate-700 py-12">
        <div className="max-w-4xl mx-auto px-4">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-50 to-blue-50 dark:from-sky-900/20 dark:to-blue-900/20 flex items-center justify-center border border-sky-200 dark:border-sky-700">
              <Zap className="w-5 h-5 text-sky-600 dark:text-sky-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-dark-text">API 按量付费</h2>
              <p className="text-sm text-slate-500 dark:text-dark-muted">用多少付多少，灵活扩展</p>
            </div>
          </div>
          <ApiPricingTable items={API_PRICING} />
          <p className="mt-3 text-xs text-slate-400 dark:text-dark-muted text-center">
            企业版和集团版用户可享受 API 调用折扣，详情联系销售团队。
          </p>
        </div>
      </div>

      {/* ── Enterprise Add-ons ────────────────────────────────── */}
      <div className="py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-50 to-indigo-50 dark:from-violet-900/20 dark:to-indigo-900/20 flex items-center justify-center border border-violet-200 dark:border-violet-700">
              <Gem className="w-5 h-5 text-violet-600 dark:text-violet-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-dark-text">企业增值服务</h2>
              <p className="text-sm text-slate-500 dark:text-dark-muted">为成长型企业量身定制</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {ENTERPRISE_ADDONS.map((addon) => (
              <AddonCard key={addon.name} addon={addon} />
            ))}
          </div>
        </div>
      </div>

      {/* ── FAQ ──────────────────────────────────────────────── */}
      <div className="bg-white dark:bg-dark-surface border-t border-slate-200 dark:border-slate-700 py-12">
        <div className="max-w-3xl mx-auto px-4">
          <h2 className="text-2xl font-bold text-center text-slate-900 dark:text-dark-text mb-8">
            常见问题
          </h2>
          <div className="space-y-3">
            {FAQS.map((faq, i) => (
              <div
                key={i}
                className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/30 overflow-hidden transition-all duration-200"
              >
                <button
                  className="w-full flex items-center justify-between px-5 py-4 text-left"
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                >
                  <span className="font-medium text-slate-900 dark:text-dark-text text-sm">{faq.q}</span>
                  <HelpCircle className={`w-4 h-4 text-slate-400 transition-transform duration-200 shrink-0 ml-2 ${openFaq === i ? 'rotate-180' : ''}`} />
                </button>
                {openFaq === i && (
                  <div className="px-5 pb-4 text-sm text-slate-600 dark:text-slate-400 leading-relaxed border-t border-slate-200 dark:border-slate-700 pt-3">
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
