import { useState } from 'react';
import {
  Key, Plus, Copy, Check, BookOpen, Download,
  Code, BarChart3, ExternalLink, Terminal,
} from 'lucide-react';

/* ---------- mock data ---------- */
const mockKeys = [
  { id: 1, name: '生产环境', prefix: 'sk_prod_a1b2', active: true, created: '2026-01-15' },
  { id: 2, name: '测试环境', prefix: 'sk_test_c3d4', active: true, created: '2026-03-22' },
  { id: 3, name: '开发环境', prefix: 'sk_dev_e5f6', active: false, created: '2026-04-10' },
];

const mockStats = { total: 284_730, month: 32_156, today: 1_084 };

/* ============================================================== */
export default function DeveloperPortal() {
  const [keys] = useState(mockKeys);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [langTab, setLangTab] = useState<'python' | 'js' | 'curl'>('python');

  const handleCopy = (id: number) => {
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  /* ---------- SDK code samples ---------- */
  const codeSamples: Record<string, string> = {
    python: `from ai_business_card import Client\n\nclient = Client(api_key="sk_...")\n# 创建名片\ncard = client.brochure.create(\n    name="张三",\n    position="CTO",\n    company="示例科技"\n)\nprint(card.share_url)`,
    js: `import { AICardClient } from 'ai-card-sdk';\n\nconst client = new AICardClient({ apiKey: 'sk_...' });\n// 创建名片\nconst card = await client.brochure.create({\n  name: '张三',\n  position: 'CTO',\n  company: '示例科技',\n});\nconsole.log(card.shareUrl);`,
    curl: `curl -X POST https://api.example.com/v1/brochure \\\n  -H "Authorization: Bearer sk_..." \\\n  -H "Content-Type: application/json" \\\n  -d '{\n    "name": "张三",\n    "position": "CTO",\n    "company": "示例科技"\n  }'`,
  };

  /* ============================================================== */
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* ---------- Header ---------- */}
      <div>
        <h1 className="text-2xl font-bold text-on-surface">开发者门户</h1>
        <p className="text-sm text-text-muted mt-1">
          集成 API 与 SDK，快速将 AI 数智名片能力接入你的应用
        </p>
      </div>

      {/* ---------- Row 1: API Keys + API Docs ---------- */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* API Keys */}
        <div className="bg-white rounded-2xl border border-border-light p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-on-surface flex items-center gap-2">
              <Key className="w-4 h-4 text-primary" /> API 密钥
            </h2>
            <button className="px-3 py-1.5 bg-primary text-white rounded-xl text-xs font-medium hover:bg-primary/90 transition-colors flex items-center gap-1">
              <Plus className="w-3.5 h-3.5" /> 创建新 Key
            </button>
          </div>
          <div className="space-y-2">
            {keys.map((k) => (
              <div
                key={k.id}
                className="flex items-center justify-between p-3 bg-slate-50 rounded-xl"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-on-surface truncate">
                      {k.name}
                    </span>
                    <span
                      className={`inline-block w-1.5 h-1.5 rounded-full ${
                        k.active ? 'bg-emerald-500' : 'bg-slate-300'
                      }`}
                    />
                  </div>
                  <code className="text-xs text-text-muted font-mono">
                    {k.prefix}****
                  </code>
                </div>
                <button
                  onClick={() => handleCopy(k.id)}
                  className="p-1.5 rounded-lg hover:bg-slate-200 text-text-muted shrink-0"
                  title="复制 Key"
                >
                  {copiedId === k.id ? (
                    <Check className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* API Docs Link */}
        <div className="bg-white rounded-2xl border border-border-light p-5">
          <h2 className="text-base font-bold text-on-surface flex items-center gap-2 mb-4">
            <BookOpen className="w-4 h-4 text-primary" /> API 文档
          </h2>
          <p className="text-sm text-text-muted mb-4">
            完整的 API 参考文档，包含认证方式、端点说明、请求/响应示例及错误码。
          </p>
          <a
            href="/api-docs"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary text-white rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            查看文档 <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* ---------- SDK / Quick Start ---------- */}
      <div className="bg-white rounded-2xl border border-border-light p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-on-surface flex items-center gap-2">
            <Terminal className="w-4 h-4 text-primary" /> 快速开始
          </h2>
          <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5">
            {['python', 'js', 'curl'].map((l) => (
              <button
                key={l}
                onClick={() => setLangTab(l as any)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  langTab === l
                    ? 'bg-white text-on-surface shadow-sm'
                    : 'text-text-muted hover:text-on-surface'
                }`}
              >
                {l === 'python' ? 'Python' : l === 'js' ? 'JavaScript' : 'cURL'}
              </button>
            ))}
          </div>
        </div>
        <pre className="bg-slate-900 text-slate-100 rounded-xl p-4 text-xs leading-relaxed overflow-x-auto font-mono">
          <code>{codeSamples[langTab]}</code>
        </pre>
        <div className="flex items-center gap-4 mt-4 text-xs text-text-muted">
          <span className="flex items-center gap-1">
            <Download className="w-3.5 h-3.5" /> Python SDK
          </span>
          <span className="flex items-center gap-1">
            <Download className="w-3.5 h-3.5" /> JavaScript SDK
          </span>
          <span className="flex items-center gap-1">
            <Code className="w-3.5 h-3.5" /> OpenAPI 规范
          </span>
        </div>
      </div>

      {/* ---------- Usage Stats ---------- */}
      <div className="bg-white rounded-2xl border border-border-light p-5">
        <h2 className="text-base font-bold text-on-surface flex items-center gap-2 mb-4">
          <BarChart3 className="w-4 h-4 text-primary" /> 使用统计
        </h2>
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: '总请求数', value: mockStats.total.toLocaleString(), color: 'from-primary to-purple-500' },
            { label: '本月', value: mockStats.month.toLocaleString(), color: 'from-amber-400 to-orange-500' },
            { label: '今日', value: mockStats.today.toLocaleString(), color: 'from-emerald-400 to-teal-500' },
          ].map((s) => (
            <div key={s.label} className="text-center p-4 bg-slate-50 rounded-xl">
              <div
                className={`w-10 h-10 rounded-xl bg-gradient-to-r ${s.color} flex items-center justify-center mx-auto mb-2`}
              >
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <p className="text-xl font-bold text-on-surface">{s.value}</p>
              <p className="text-xs text-text-muted mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
