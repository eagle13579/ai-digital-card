import { useState } from 'react';
import {
  Sparkles, X, Loader2, FileText, Building2, Star, Quote,
  PenTool, CheckCircle2, AlertTriangle, BarChart3,
  RefreshCw, Lightbulb, ChevronDown, ChevronUp,
} from 'lucide-react';
import { api } from '../api/client';
import { useT } from '../i18n';

// ============================================================
// 类型
// ============================================================

type WritePurpose = 'bio' | 'company' | 'recommendation' | 'slogan';

interface WriteResult {
  [key: string]: string;
}

interface OptimizeData {
  overall_score: number;
  completeness: { score: number; level: string; missing_fields: string[] };
  keyword_coverage: { score: number; matched_keywords: string[]; suggested_keywords: string[]; total_keywords: number };
  professionalism: { score: number; issues: { field: string; issue: string; severity: string }[]; suggestions: string[] };
  top_priorities: string[];
}

interface AIAssistantProps {
  /** 当前正在编辑的名片字段（用于文案生成和优化） */
  fields?: Record<string, string>;
  /** 当前查看的名片ID（用于优化分析） */
  brochureId?: number | null;
  /** 关闭回调 */
  onClose: () => void;
  /** 将生成的文案应用到字段 */
  onApplyCopy?: (purpose: string, content: string) => void;
  /** 行业名称（可选，用于关键词分析） */
  industry?: string;
}

// ============================================================
// 文案用途配置
// ============================================================

const WRITE_PURPOSES: { key: WritePurpose; label: string; icon: React.ReactNode; desc: string }[] = [
  { key: 'bio', label: '个人简介', icon: <FileText className="w-4 h-4" />, desc: '生成一段简洁的个人简介' },
  { key: 'company', label: '公司介绍', icon: <Building2 className="w-4 h-4" />, desc: '生成专业的公司介绍' },
  { key: 'recommendation', label: '推荐语', icon: <Star className="w-4 h-4" />, desc: '生成推荐或评价语' },
  { key: 'slogan', label: '名片标语', icon: <Quote className="w-4 h-4" />, desc: '生成一句话个人标语' },
];

// ============================================================
// 主组件
// ============================================================

export default function AIAssistant({ fields, brochureId, onClose, onApplyCopy, industry }: AIAssistantProps) {
  const t = useT();
  const [activeTab, setActiveTab] = useState<'write' | 'optimize'>('write');

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      {/* Animation styles */}
      <style>{`
        @keyframes slideUp {
          from { transform: translateY(100%); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      {/* Panel */}
      <div
        className="relative w-full max-w-lg max-h-[85vh] bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl overflow-hidden flex flex-col"
        style={{
          animation: 'slideUp 0.3s ease-out',
        }}
      >
        {/* Header */}
        <div className="shrink-0 flex items-center justify-between px-4 py-3 border-b border-border-light">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="text-base font-bold text-on-surface">{t('ai.assistant.title')}</h2>
              <p className="text-[10px] text-text-muted">{t('ai.assistant.subtitle')}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="shrink-0 flex border-b border-border-light">
          <button
            onClick={() => setActiveTab('write')}
            className={`flex-1 py-2.5 text-sm font-medium flex items-center justify-center gap-1.5 transition-colors ${
              activeTab === 'write'
                ? 'text-primary border-b-2 border-primary'
                : 'text-text-muted hover:text-on-surface'
            }`}
          >
            <PenTool className="w-4 h-4" />
            {t('ai.assistant.writeTab')}
          </button>
          <button
            onClick={() => setActiveTab('optimize')}
            className={`flex-1 py-2.5 text-sm font-medium flex items-center justify-center gap-1.5 transition-colors ${
              activeTab === 'optimize'
                ? 'text-primary border-b-2 border-primary'
                : 'text-text-muted hover:text-on-surface'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            {t('ai.assistant.optimizeTab')}
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'write' ? (
            <WriteTab fields={fields} onApplyCopy={onApplyCopy} />
          ) : (
            <OptimizeTab brochureId={brochureId} industry={industry} />
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// 写作 Tab
// ============================================================

function WriteTab({
  fields,
  onApplyCopy,
}: {
  fields?: Record<string, string>;
  onApplyCopy?: (purpose: string, content: string) => void;
}) {
  const t = useT();
  const [selectedPurpose, setSelectedPurpose] = useState<WritePurpose>('bio');
  const [customInputs, setCustomInputs] = useState<Record<string, string>>({});
  const [results, setResults] = useState<WriteResult>({});
  const [loading, setLoading] = useState<WritePurpose | null>(null);
  const [loadingAll, setLoadingAll] = useState(false);
  const [showInputs, setShowInputs] = useState(false);

  const getFieldValue = (key: string): string => {
    return customInputs[key] || fields?.[key] || '';
  };

  const handleGenerate = async (purpose: WritePurpose) => {
    setLoading(purpose);
    try {
      const body: Record<string, string> = {
        purpose,
        name: getFieldValue('name'),
        position: getFieldValue('position'),
        company: getFieldValue('company'),
        industry: getFieldValue('industry'),
        skills: getFieldValue('skills'),
        description: getFieldValue('description'),
        highlights: getFieldValue('highlights'),
        relationship: getFieldValue('relationship'),
        core_value: getFieldValue('core_value'),
      };
      const res = await api.post<{ purpose: string; content: string }>('/ai/assist/write', body);
      if (res.code === 200 && res.data) {
        setResults((prev) => ({ ...prev, [purpose]: res.data!.content }));
      } else {
        setResults((prev) => ({ ...prev, [purpose]: `生成失败: ${res.message}` }));
      }
    } catch (e: any) {
      setResults((prev) => ({ ...prev, [purpose]: `请求失败: ${e.message}` }));
    } finally {
      setLoading(null);
    }
  };

  const handleGenerateAll = async () => {
    setLoadingAll(true);
    try {
      const body: Record<string, string> = {
        name: getFieldValue('name'),
        position: getFieldValue('position'),
        company: getFieldValue('company'),
        industry: getFieldValue('industry'),
        skills: getFieldValue('skills'),
        description: getFieldValue('description'),
        highlights: getFieldValue('highlights'),
        relationship: getFieldValue('relationship'),
        core_value: getFieldValue('core_value'),
      };
      const res = await api.post<Record<string, string>>('/ai/assist/write/all', body);
      if (res.code === 200 && res.data) {
        setResults(res.data);
      } else {
        console.error('批量生成失败:', res.message);
      }
    } catch (e: any) {
      console.error('批量生成失败:', e);
    } finally {
      setLoadingAll(false);
    }
  };

  const handleApply = (purpose: string, content: string) => {
    if (onApplyCopy) {
      onApplyCopy(purpose, content);
    }
  };

  return (
    <div className="space-y-4">
      {/* Purpose selector */}
      <div className="grid grid-cols-2 gap-2">
        {WRITE_PURPOSES.map((p) => (
          <button
            key={p.key}
            onClick={() => setSelectedPurpose(p.key)}
            className={`p-3 rounded-xl border text-left transition-all ${
              selectedPurpose === p.key
                ? 'border-primary bg-primary/5 ring-1 ring-primary/30'
                : 'border-border-light hover:border-primary/50'
            }`}
          >
            <div className="flex items-center gap-2">
              <span className={`${selectedPurpose === p.key ? 'text-primary' : 'text-text-muted'}`}>
                {p.icon}
              </span>
              <span className={`text-sm font-medium ${selectedPurpose === p.key ? 'text-primary' : 'text-on-surface'}`}>
                {t('ai.' + p.key)}
              </span>
            </div>
            <p className="text-[10px] text-text-muted mt-1">{t('ai.' + p.key + '.desc')}</p>
          </button>
        ))}
      </div>

      {/* Custom inputs toggle */}
      <button
        onClick={() => setShowInputs(!showInputs)}
        className="flex items-center gap-1 text-xs text-text-muted hover:text-on-surface transition-colors"
      >
        {showInputs ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {showInputs ? t('ai.collapseInputs') : t('ai.expandInputs')}
      </button>

      {showInputs && (
        <div className="grid grid-cols-2 gap-2 p-3 bg-slate-50 rounded-xl">
          <input
            value={customInputs.name || fields?.name || ''}
            onChange={(e) => setCustomInputs((p) => ({ ...p, name: e.target.value }))}
            placeholder={t('ai.name')}
            className="px-2.5 py-1.5 rounded-lg border border-border-light bg-white text-xs focus:outline-none focus:ring-1 focus:ring-primary/30"
          />
          <input
            value={customInputs.position || fields?.position || ''}
            onChange={(e) => setCustomInputs((p) => ({ ...p, position: e.target.value }))}
            placeholder={t('ai.position')}
            className="px-2.5 py-1.5 rounded-lg border border-border-light bg-white text-xs focus:outline-none focus:ring-1 focus:ring-primary/30"
          />
          <input
            value={customInputs.company || fields?.company || ''}
            onChange={(e) => setCustomInputs((p) => ({ ...p, company: e.target.value }))}
            placeholder={t('ai.company')}
            className="px-2.5 py-1.5 rounded-lg border border-border-light bg-white text-xs focus:outline-none focus:ring-1 focus:ring-primary/30"
          />
          <input
            value={customInputs.industry || fields?.industry || ''}
            onChange={(e) => setCustomInputs((p) => ({ ...p, industry: e.target.value }))}
            placeholder={t('ai.industry')}
            className="px-2.5 py-1.5 rounded-lg border border-border-light bg-white text-xs focus:outline-none focus:ring-1 focus:ring-primary/30"
          />
        </div>
      )}

      {/* Generate buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => handleGenerate(selectedPurpose)}
          disabled={loading === selectedPurpose}
          className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-primary to-purple-600 text-white text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading === selectedPurpose ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4" />
          )}
          {t('ai.generate', { label: t('ai.' + selectedPurpose) })}
        </button>
        <button
          onClick={handleGenerateAll}
          disabled={loadingAll}
          className="px-3 py-2.5 rounded-xl border border-border-light text-on-surface text-sm font-medium hover:bg-slate-50 transition-colors disabled:opacity-50 flex items-center gap-1.5"
          title={t('ai.generateAll.tooltip')}
        >
          {loadingAll ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          {t('ai.generateAll')}
        </button>
      </div>

      {/* Results */}
      {Object.keys(results).length > 0 && (
        <div className="space-y-3">
          {Object.entries(results).map(([purpose, content]) => {
            if (!content) return null;
            const label = WRITE_PURPOSES.find(p => p.key === purpose)?.label || purpose;
            return (
              <div key={purpose} className="bg-slate-50 rounded-xl p-3">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-text-muted">{label}</span>
                  {onApplyCopy && !content.startsWith('生成失败') && !content.startsWith('请求失败') && !content.startsWith('【') && (
                    <button
                      onClick={() => handleApply(purpose, content)}
                      className="text-xs text-primary hover:text-primary-container transition-colors flex items-center gap-1"
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      {t('ai.applyToCard')}
                    </button>
                  )}
                </div>
                <p className={`text-sm ${content.startsWith('生成失败') || content.startsWith('请求失败') || content.startsWith('【') ? 'text-rose-500' : 'text-on-surface'}`}>
                  {content.startsWith('【') ? content.replace(/[【】]/g, '') : content}
                </p>
              </div>
            );
          })}
        </div>
      )}

      {/* Hint */}
      {Object.keys(results).length === 0 && (
        <div className="text-center py-8">
          <div className="w-12 h-12 rounded-full bg-primary/5 flex items-center justify-center mx-auto mb-3">
            <Sparkles className="w-6 h-6 text-primary/40" />
          </div>
          <p className="text-xs text-text-muted">{t('ai.writeHint')}</p>
          <p className="text-[10px] text-text-muted mt-1">{t('ai.writeHint.desc')}</p>
        </div>
      )}
    </div>
  );
}

// ============================================================
// 优化 Tab
// ============================================================

function OptimizeTab({
  brochureId,
  industry,
}: {
  brochureId?: number | null;
  industry?: string;
}) {
  const t = useT();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<OptimizeData | null>(null);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    if (!brochureId) {
      setError(t('ai.selectCardFirst'));
      return;
    }
    setLoading(true);
    setError('');
    try {
      const url = `/ai/assist/optimize/${brochureId}${industry ? `?industry=${encodeURIComponent(industry)}` : ''}`;
      const res = await api.get<OptimizeData>(url);
      if (res.code === 200 && res.data) {
        setData(res.data);
      } else {
        setError(res.message || t('ai.analyzeFailed'));
      }
    } catch (e: any) {
      setError(e.message || t('ai.requestFailed'));
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-emerald-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-rose-600';
  };

  const getScoreBg = (score: number): string => {
    if (score >= 80) return 'bg-emerald-50 border-emerald-200';
    if (score >= 60) return 'bg-amber-50 border-amber-200';
    return 'bg-rose-50 border-rose-200';
  };

  const getLevelColor = (level: string): string => {
    switch (level) {
      case '优秀': return 'text-emerald-600 bg-emerald-50';
      case '良好': return 'text-blue-600 bg-blue-50';
      case '一般': return 'text-amber-600 bg-amber-50';
      default: return 'text-rose-600 bg-rose-50';
    }
  };

  if (!brochureId) {
    return (
      <div className="text-center py-12">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
          <BarChart3 className="w-6 h-6 text-text-muted" />
        </div>
        <p className="text-sm text-text-muted">{t('ai.viewCardDetail')}</p>
        <p className="text-xs text-text-muted mt-1">{t('ai.openInDetail')}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Analyze button */}
      {!data && (
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="w-full py-3 rounded-xl bg-gradient-to-r from-primary to-purple-600 text-white text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <BarChart3 className="w-4 h-4" />
          )}
          {t('ai.startAnalyze')}
        </button>
      )}

      {/* Error */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 text-xs text-rose-700 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center py-8">
          <Loader2 className="w-6 h-6 text-primary animate-spin" />
          <p className="text-xs text-text-muted mt-2">{t('ai.analyzing')}</p>
        </div>
      )}

      {/* Results */}
      {data && (
        <div className="space-y-4">
          {/* Overall score */}
          <div className={`rounded-xl p-4 border ${getScoreBg(data.overall_score)}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-bold text-on-surface">{t('ai.overallScore')}</span>
              <span className={`text-2xl font-bold ${getScoreColor(data.overall_score)}`}>
                {data.overall_score}
              </span>
            </div>
            <div className="w-full h-2 bg-white/60 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  data.overall_score >= 80 ? 'bg-emerald-500' : data.overall_score >= 60 ? 'bg-amber-500' : 'bg-rose-500'
                }`}
                style={{ width: `${data.overall_score}%` }}
              />
            </div>
          </div>

          {/* Detail scores */}
          <div className="grid grid-cols-3 gap-2">
            {/* Completeness */}
            <div className="bg-slate-50 rounded-xl p-2.5 text-center">
              <p className="text-[10px] text-text-muted mb-1">{t('ai.completeness')}</p>
              <p className={`text-lg font-bold ${getScoreColor(data.completeness.score)}`}>
                {data.completeness.score}
              </p>
              <span className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-medium mt-1 ${getLevelColor(data.completeness.level)}`}>
                {data.completeness.level}
              </span>
            </div>
            {/* Keyword coverage */}
            <div className="bg-slate-50 rounded-xl p-2.5 text-center">
              <p className="text-[10px] text-text-muted mb-1">{t('ai.keywords')}</p>
              <p className={`text-lg font-bold ${getScoreColor(data.keyword_coverage.score)}`}>
                {data.keyword_coverage.score}
              </p>
              <p className="text-[9px] text-text-muted mt-1">
                {data.keyword_coverage.matched_keywords.length}/{data.keyword_coverage.total_keywords}
              </p>
            </div>
            {/* Professionalism */}
            <div className="bg-slate-50 rounded-xl p-2.5 text-center">
              <p className="text-[10px] text-text-muted mb-1">{t('ai.professionalism')}</p>
              <p className={`text-lg font-bold ${getScoreColor(data.professionalism.score)}`}>
                {data.professionalism.score}
              </p>
              <p className="text-[9px] text-text-muted mt-1">
                {t('ai.issues', { n: data.professionalism.issues.length })}
              </p>
            </div>
          </div>

          {/* Top priorities */}
          <div>
            <h3 className="text-xs font-bold text-on-surface mb-2 flex items-center gap-1.5">
              <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
              {t('ai.optimizeSuggestions')}
            </h3>
            <div className="space-y-1.5">
              {data.top_priorities.map((tip, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-on-surface bg-amber-50 rounded-xl p-2.5">
                  <span className="w-4 h-4 rounded-full bg-amber-200 text-amber-700 flex items-center justify-center text-[9px] font-bold shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <span>{tip}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Missing fields */}
          {data.completeness.missing_fields.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-on-surface mb-2">{t('ai.missingFields')}</h3>
              <div className="flex flex-wrap gap-1.5">
                {data.completeness.missing_fields.map((f) => (
                  <span key={f} className="px-2 py-0.5 rounded-full bg-rose-50 text-rose-600 text-[10px] font-medium">
                    {f}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Suggested keywords */}
          {data.keyword_coverage.suggested_keywords.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-on-surface mb-2">{t('ai.suggestedKeywords')}</h3>
              <div className="flex flex-wrap gap-1.5">
                {data.keyword_coverage.suggested_keywords.map((kw) => (
                  <span key={kw} className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 text-[10px] font-medium">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Re-analyze */}
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="w-full py-2 rounded-xl border border-border-light text-on-surface text-sm hover:bg-slate-50 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {t('ai.reanalyze')}
          </button>
        </div>
      )}
    </div>
  );
}
