import { useState } from 'react';
import { Shield, BookOpen, Code, ChevronRight, Copy, Check } from 'lucide-react';

const endpointGroups = [
  { label: '名片 (Brochure)', color: 'from-primary to-purple-500', endpoints: [
    { m: 'POST', p: '/api/v1/brochure', d: '创建新名片，支持 AI 自动补全' },
    { m: 'GET', p: '/api/v1/brochure/:id', d: '获取单张名片详情' },
    { m: 'PUT', p: '/api/v1/brochure/:id', d: '更新名片信息' },
  ]},
  { label: '用户 (User)', color: 'from-amber-400 to-orange-500', endpoints: [
    { m: 'GET', p: '/api/v1/user/profile', d: '获取当前用户资料' },
    { m: 'PUT', p: '/api/v1/user/profile', d: '更新用户资料' },
  ]},
  { label: '匹配 (Match)', color: 'from-emerald-400 to-teal-500', endpoints: [
    { m: 'POST', p: '/api/v1/match/supply', d: '提交供应需求并匹配' },
    { m: 'GET', p: '/api/v1/match/results', d: '获取匹配结果列表' },
  ]},
  { label: 'AI', color: 'from-rose-400 to-pink-500', endpoints: [
    { m: 'POST', p: '/api/v1/ai/generate', d: 'AI 生成名片内容' },
    { m: 'POST', p: '/api/v1/ai/enhance', d: 'AI 润色名片文案' },
  ]},
  { label: '管理 (Admin)', color: 'from-slate-500 to-slate-700', endpoints: [
    { m: 'GET', p: '/api/v1/admin/analytics', d: '获取平台统计数据' },
    { m: 'GET', p: '/api/v1/admin/users', d: '用户管理列表' },
  ]},
];

const METHOD_COLORS: Record<string, string> = {
  GET: 'bg-emerald-500', POST: 'bg-blue-500', PUT: 'bg-amber-500', DELETE: 'bg-rose-500',
};

const codeMap: Record<string, string> = {
  curl: `curl -X GET "https://api.example.com/api/v1/brochure/123" \\\n  -H "Authorization: Bearer **" \\\n  -H "Content-Type: application/json"`,
  python: `import requests\n\nheaders = {\n    "Authorization": "Bearer **",\n    "Content-Type": "application/json",\n}\nresp = requests.get(\n    "https://api.example.com/api/v1/brochure/123",\n    headers=headers,\n)\nprint(resp.json())`,
  js: `const resp = await fetch(\n  "https://api.example.com/api/v1/brochure/123",\n  {\n    headers: {\n      Authorization: "Bearer **",\n      "Content-Type": "application/json",\n    },\n  },\n);\nconst data = await resp.json();\nconsole.log(data);`,
};

export default function ApiDocs() {
  const [activeGroup, setActiveGroup] = useState(0);
  const [codeLang, setCodeLang] = useState('curl');
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try { await navigator.clipboard.writeText(codeMap[codeLang]); } catch {
      console.warn('[ApiDocs] Copy to clipboard failed');
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const group = endpointGroups[activeGroup];
  const langs = [
    { k: 'curl', label: 'cURL' },
    { k: 'python', label: 'Python' },
    { k: 'js', label: 'JavaScript' },
  ];

  const methodBadge = (m: string) => (
    <span className={`shrink-0 px-2 py-0.5 rounded text-[11px] font-bold text-white ${METHOD_COLORS[m] || 'bg-slate-500'}`}>
      {m}
    </span>
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-on-surface flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-primary" /> API 参考文档
        </h1>
        <p className="text-sm text-text-muted mt-1">
          AI 数智名片开放 API — 基于 RESTful 设计，返回 JSON 格式数据
        </p>
      </div>

      {/* Auth */}
      <div className="bg-white rounded-2xl border border-border-light p-5">
        <h2 className="text-base font-bold text-on-surface flex items-center gap-2 mb-3">
          <Shield className="w-4 h-4 text-primary" /> 认证方式
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[{ title: 'JWT Bearer', desc: '用户登录后获取 JWT Token' }, { title: 'API Key', desc: '服务端调用使用 API Key' }].map((a) => (
            <div key={a.title} className="p-4 bg-slate-50 rounded-xl">
              <code className="text-xs font-mono text-primary font-bold">{a.title}</code>
              <p className="text-xs text-text-muted mt-1">
                {a.desc}，在请求头中传递<br />
                <code className="text-[11px] font-mono bg-slate-200 px-1.5 py-0.5 rounded">Authorization: Bearer **</code>
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Endpoints + Code */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="md:col-span-1 bg-white rounded-2xl border border-border-light p-2 space-y-1">
          {endpointGroups.map((g, i) => (
            <button key={g.label} onClick={() => setActiveGroup(i)}
              className={`w-full text-left px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                i === activeGroup ? 'bg-primary/10 text-primary' : 'text-text-muted hover:bg-slate-50 hover:text-on-surface'
              }`}>
              {g.label}
            </button>
          ))}
        </div>

        <div className="md:col-span-4 space-y-4">
          <div className="bg-white rounded-2xl border border-border-light p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${group.color}`} />
              <h2 className="text-base font-bold text-on-surface">{group.label}</h2>
            </div>
            <div className="space-y-2">
              {group.endpoints.map((ep) => (
                <div key={ep.p} className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
                  {methodBadge(ep.m)}
                  <div className="min-w-0 flex-1">
                    <code className="text-xs font-mono text-on-surface font-medium break-all">{ep.p}</code>
                    <p className="text-xs text-text-muted mt-0.5">{ep.d}</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-text-muted shrink-0 mt-0.5" />
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-border-light p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-on-surface flex items-center gap-2">
                <Code className="w-4 h-4 text-primary" /> 代码示例
              </h3>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5">
                  {langs.map((t) => (
                    <button key={t.k} onClick={() => setCodeLang(t.k)}
                      className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                        codeLang === t.k ? 'bg-white text-on-surface shadow-card' : 'text-text-muted hover:text-on-surface'
                      }`}>
                      {t.label}
                    </button>
                  ))}
                </div>
                <button onClick={handleCopy} className="p-1.5 rounded-lg hover:bg-slate-100 text-text-muted" title="复制代码" aria-label="复制代码">
                  {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <pre className="bg-slate-900 text-slate-100 rounded-xl p-4 text-xs leading-relaxed overflow-x-auto font-mono">
              <code>{codeMap[codeLang]}</code>
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
