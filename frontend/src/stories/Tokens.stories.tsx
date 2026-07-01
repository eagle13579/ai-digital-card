import type { Meta, StoryObj } from '@storybook/react';

/**
 * 设计 Token — 展示页面
 *
 * 集中展示 AI 数智名片项目的所有设计 Token，包括：
 * - 品牌色板（Primary / Secondary / Error 等）
 * - 表层色板（Surface / Neutral / Dark）
 * - 字体体系（Sans / Manrope / Inter）
 * - 圆角规范
 * - 阴影层级
 * - 间距比例
 * - 动画时长
 */

const meta: Meta = {
  title: 'Design System/Tokens',
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          '## 🎨 设计 Token 总览\n\n本页面集中展示了 AI 数智名片项目的所有设计 Token，包括颜色、字体、圆角、阴影等核心设计变量。所有 Token 在 `src/index.css` 中使用 Tailwind v4 的 `@theme` 指令定义。',
      },
    },
  },
};

export default meta;

// ─── 颜色色板数据 ──────────────────────────────────────

interface ColorToken {
  name: string;
  token: string;
  value: string;
  hex: string;
  textClass: string;
}

const brandColors: ColorToken[] = [
  { name: 'Primary', token: '--color-primary', value: 'sky-600', hex: '#0284c7', textClass: 'text-white' },
  { name: 'Primary Container', token: '--color-primary-container', value: 'sky-500', hex: '#0ea5e9', textClass: 'text-white' },
  { name: 'Primary Light', token: '--color-primary-light', value: 'sky-100', hex: '#e0f2fe', textClass: 'text-sky-800' },
  { name: 'Secondary', token: '--color-secondary', value: 'slate-600', hex: '#475569', textClass: 'text-white' },
  { name: 'Success', token: '--color-success', value: 'emerald-500', hex: '#10b981', textClass: 'text-white' },
  { name: 'Warning', token: '--color-warning', value: 'amber-500', hex: '#f59e0b', textClass: 'text-white' },
  { name: 'Error', token: '--color-error', value: 'rose-600', hex: '#e11d48', textClass: 'text-white' },
];

const surfaceColors: ColorToken[] = [
  { name: 'Neutral BG', token: '--color-neutral-bg', value: 'slate-50', hex: '#f8fafc', textClass: 'text-slate-700' },
  { name: 'Surface', token: '--color-surface', value: 'white', hex: '#ffffff', textClass: 'text-slate-700' },
  { name: 'On Surface', token: '--color-on-surface', value: 'slate-800', hex: '#1e293b', textClass: 'text-white' },
  { name: 'Text Muted', token: '--color-text-muted', value: 'slate-400', hex: '#94a3b8', textClass: 'text-white' },
  { name: 'Border Light', token: '--color-border-light', value: 'slate-200', hex: '#e2e8f0', textClass: 'text-slate-700' },
];

const darkColors: ColorToken[] = [
  { name: 'Dark BG', token: '--color-dark-bg', value: '—', hex: '#0f172a', textClass: 'text-white' },
  { name: 'Dark Surface', token: '--color-dark-surface', value: '—', hex: '#1e293b', textClass: 'text-white' },
  { name: 'Dark Border', token: '--color-dark-border', value: '—', hex: '#334155', textClass: 'text-white' },
  { name: 'Dark Text', token: '--color-dark-text', value: '—', hex: '#f1f5f9', textClass: 'text-slate-800' },
  { name: 'Dark Muted', token: '--color-dark-muted', value: '—', hex: '#94a3b8', textClass: 'text-white' },
];

// ─── 字体数据 ──────────────────────────────────────────

interface FontToken {
  name: string;
  token: string;
  fontFamily: string;
  fallback: string;
}

const fontTokens: FontToken[] = [
  { name: 'Sans (中文字体)', token: '--font-sans', fontFamily: 'Noto Sans SC, Inter', fallback: 'ui-sans-serif, system-ui' },
  { name: 'Manrope (数字/英文)', token: '--font-manrope', fontFamily: 'Manrope, Noto Sans SC', fallback: 'sans-serif' },
  { name: 'Inter (英文/数字)', token: '--font-inter', fontFamily: 'Inter', fallback: 'ui-sans-serif, system-ui' },
];

// ─── 圆角数据 ──────────────────────────────────────────

interface RadiusToken {
  name: string;
  class: string;
  value: string;
}

const radiusTokens: RadiusToken[] = [
  { name: '小圆角', class: 'rounded-lg', value: '8px' },
  { name: '中圆角', class: 'rounded-xl', value: '12px' },
  { name: '大圆角', class: 'rounded-2xl', value: '16px' },
  { name: '全圆角', class: 'rounded-full', value: '9999px' },
];

// ─── 阴影数据 ──────────────────────────────────────────

interface ShadowToken {
  name: string;
  class: string;
  value: string;
}

const shadowTokens: ShadowToken[] = [
  { name: '卡片阴影', class: 'shadow-sm', value: '0 1px 2px 0 rgb(0 0 0 / 0.05)' },
  { name: '升起阴影', class: 'shadow-md', value: '0 4px 6px -1px rgb(0 0 0 / 0.1)' },
  { name: '弹窗阴影', class: 'shadow-lg', value: '0 10px 15px -3px rgb(0 0 0 / 0.1)' },
  { name: '下拉阴影', class: 'shadow-xl', value: '0 20px 25px -5px rgb(0 0 0 / 0.1)' },
];

// ─── 间距数据 ──────────────────────────────────────────

interface SpacingToken {
  name: string;
  class: string;
  value: string;
}

const spacingTokens: SpacingToken[] = [
  { name: 'XS', class: 'p-1', value: '4px' },
  { name: 'SM', class: 'p-2', value: '8px' },
  { name: 'MD', class: 'p-4', value: '16px' },
  { name: 'LG', class: 'p-6', value: '24px' },
  { name: 'XL', class: 'p-8', value: '32px' },
  { name: '2XL', class: 'p-10', value: '40px' },
];

// ─── 动画时长数据 ──────────────────────────────────────

interface AnimationToken {
  name: string;
  class: string;
  value: string;
  description: string;
}

const animationTokens: AnimationToken[] = [
  { name: '快速', class: 'duration-150', value: '150ms', description: '悬浮、点击反馈' },
  { name: '标准', class: 'duration-200', value: '200ms', description: '按钮、卡片过渡' },
  { name: '中速', class: 'duration-300', value: '300ms', description: '弹窗、面板展开' },
  { name: '慢速', class: 'duration-500', value: '500ms', description: '页面切换' },
];

// ─── 展示组件 ──────────────────────────────────────────

function ColorSwatch({ name, token, hex, textClass }: ColorToken) {
  return (
    <div className="flex items-center gap-3 p-3 bg-surface rounded-xl border border-border-light">
      <div
        className="w-12 h-12 rounded-xl shrink-0 border border-border-light"
        style={{ backgroundColor: hex }}
      />
      <div className="min-w-0 flex-1">
        <div className="text-sm font-semibold text-on-surface">{name}</div>
        <div className="text-xs text-text-muted font-mono mt-0.5">{token}</div>
        <div className="text-xs text-text-muted mt-0.5">
          {hex}
          <span className="ml-2 opacity-60">{token.replace('--color-', '')}</span>
        </div>
      </div>
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-lg font-bold text-on-surface mb-4 flex items-center gap-2">
      {children}
    </h2>
  );
}

function Divider() {
  return <div className="border-t border-border-light my-8" />;
}

export const All: StoryObj = {
  render: () => (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-800 text-on-surface" style={{ fontFamily: 'var(--font-manrope)' }}>
          🎨 设计 Token
        </h1>
        <p className="text-sm text-text-muted mt-1">
          基于 Tailwind v4 <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">@theme</code> 指令定义的设计变量
        </p>
      </div>

      {/* ================================================================ */}
      {/* Brand Colors */}
      {/* ================================================================ */}
      <section>
        <SectionTitle>🎯 品牌色板</SectionTitle>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {brandColors.map((c) => (
            <ColorSwatch key={c.name} {...c} />
          ))}
        </div>
      </section>

      <Divider />

      {/* ================================================================ */}
      {/* Surface Colors */}
      {/* ================================================================ */}
      <section>
        <SectionTitle>🧊 表层色板</SectionTitle>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {surfaceColors.map((c) => (
            <ColorSwatch key={c.name} {...c} />
          ))}
        </div>
      </section>

      <Divider />

      {/* ================================================================ */}
      {/* Dark Mode */}
      {/* ================================================================ */}
      <section>
        <SectionTitle>🌙 暗黑模式</SectionTitle>
        <p className="text-sm text-text-muted mb-4">
          通过给父容器添加 <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">.dark</code> 类切换。
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {darkColors.map((c) => (
            <ColorSwatch key={c.name} {...c} />
          ))}
        </div>

        {/* Dark mode preview */}
        <div className="mt-4 p-6 rounded-2xl" style={{ backgroundColor: '#0f172a' }}>
          <p className="text-sm text-white/80 mb-3">暗黑模式预览</p>
          <div className="flex gap-3">
            <button className="px-4 py-2 rounded-xl text-sm font-medium bg-[#0ea5e9] text-white">
              Primary
            </button>
            <button
              className="px-4 py-2 rounded-xl text-sm font-medium"
              style={{ backgroundColor: '#1e293b', color: '#f1f5f9', border: '1px solid #334155' }}
            >
              Outline
            </button>
          </div>
        </div>
      </section>

      <Divider />

      {/* ================================================================ */}
      {/* Typography */}
      {/* ================================================================ */}
      <section>
        <SectionTitle>🔤 字体体系</SectionTitle>
        <div className="space-y-4">
          {fontTokens.map((font) => (
            <div
              key={font.name}
              className="p-4 bg-surface rounded-xl border border-border-light"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-on-surface">{font.name}</span>
                <span className="text-xs text-text-muted font-mono">{font.token}</span>
              </div>
              <p
                className="text-xl text-on-surface"
                style={{ fontFamily: `var(${font.token})` }}
              >
                AI 数智名片 ABC 123
              </p>
              <p className="text-xs text-text-muted mt-1">
                {font.fontFamily}, {font.fallback}
              </p>
            </div>
          ))}
        </div>
      </section>

      <Divider />

      {/* ================================================================ */}
      {/* Border Radius */}
      {/* ================================================================ */}
      <section>
        <SectionTitle>🔲 圆角规范</SectionTitle>
        <div className="flex flex-wrap gap-4">
          {radiusTokens.map((r) => (
            <div key={r.name} className="flex flex-col items-center gap-2">
              <div
                className={`w-16 h-16 bg-primary/20 border-2 border-primary ${r.class}`}
              />
              <span className="text-xs font-medium text-on-surface">{r.name}</span>
              <span className="text-xs text-text-muted font-mono">{r.value}</span>
              <span className="text-xs text-text-muted font-mono">{r.class}</span>
            </div>
          ))}
        </div>
      </section>

      <Divider />

      {/* ================================================================ */}
      {/* Shadows */}
      {/* ================================================================ */}
      <section>
        <SectionTitle>👤 阴影层级</SectionTitle>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {shadowTokens.map((s) => (
            <div
              key={s.name}
              className={`p-4 bg-surface rounded-xl border border-border-light ${s.class}`}
            >
              <div className="text-sm font-semibold text-on-surface mb-1">{s.name}</div>
              <div className="text-xs text-text-muted font-mono">{s.class}</div>
              <div className="text-xs text-text-muted mt-1 break-all">{s.value}</div>
            </div>
          ))}
        </div>
      </section>

      <Divider />

      {/* ================================================================ */}
      {/* Spacing */}
      {/* ================================================================ */}
      <section>
        <SectionTitle>📐 间距比例</SectionTitle>
        <div className="space-y-3">
          {spacingTokens.map((s) => (
            <div
              key={s.name}
              className="flex items-center gap-4 p-3 bg-surface rounded-xl border border-border-light"
            >
              <span className="text-sm font-medium text-on-surface w-12 shrink-0">{s.name}</span>
              <div
                className="h-8 bg-primary/30 rounded-lg border border-primary/50"
                style={{ width: s.value }}
              />
              <span className="text-xs text-text-muted font-mono ml-auto">{s.value}</span>
              <span className="text-xs text-text-muted font-mono">{s.class}</span>
            </div>
          ))}
        </div>
      </section>

      <Divider />

      {/* ================================================================ */}
      {/* Animation */}
      {/* ================================================================ */}
      <section>
        <SectionTitle>⚡ 动画时长</SectionTitle>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {animationTokens.map((a) => (
            <div
              key={a.name}
              className="p-4 bg-surface rounded-xl border border-border-light text-center"
            >
              <div className="text-sm font-semibold text-on-surface mb-1">{a.name}</div>
              <div className="text-xs text-text-muted font-mono mb-2">{a.value}</div>
              <div className="w-10 h-10 mx-auto bg-primary rounded-lg animate-pulse" />
              <p className="text-xs text-text-muted mt-2">{a.description}</p>
            </div>
          ))}
        </div>
      </section>

      <Divider />

      {/* ================================================================ */}
      {/* Usage */}
      {/* ================================================================ */}
      <section>
        <SectionTitle>📖 使用方式</SectionTitle>
        <div className="bg-slate-900 rounded-2xl p-5 overflow-x-auto">
          <pre className="text-sm text-slate-200 font-mono leading-relaxed">
            <code>{`/* 在 Tailwind CSS 中使用 */
<button className="bg-primary text-white rounded-xl px-4 py-2">
  Primary 按钮
</button>

/* 在 CSS 中使用 */
.custom-element {
  color: var(--color-primary);
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  font-family: var(--font-sans);
}

/* 自定义组件 (clsx 模式) */
import clsx from 'clsx';
<div className={clsx(
  'bg-surface rounded-2xl',
  'border border-border-light',
  'p-4 sm:p-6',
)} />`}</code>
          </pre>
        </div>
      </section>

      {/* Footer spacer */}
      <div className="h-8" />
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story: '完整的设计 Token 展示，涵盖所有色板、字体、圆角、阴影、间距和动画规范。',
      },
    },
  },
};
