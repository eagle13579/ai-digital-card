import{j as e}from"./iframe-BgyFVukn.js";import"./preload-helper-Dp1pzeXC.js";const y={title:"Design System/Tokens",parameters:{layout:"padded",docs:{description:{component:"## 🎨 设计 Token 总览\n\n本页面集中展示了 AI 数智名片项目的所有设计 Token，包括颜色、字体、圆角、阴影等核心设计变量。所有 Token 在 `src/index.css` 中使用 Tailwind v4 的 `@theme` 指令定义。"}}}},m=[{name:"Primary",token:"--color-primary",value:"sky-600",hex:"#0284c7",textClass:"text-white"},{name:"Primary Container",token:"--color-primary-container",value:"sky-500",hex:"#0ea5e9",textClass:"text-white"},{name:"Primary Light",token:"--color-primary-light",value:"sky-100",hex:"#e0f2fe",textClass:"text-sky-800"},{name:"Secondary",token:"--color-secondary",value:"slate-600",hex:"#475569",textClass:"text-white"},{name:"Success",token:"--color-success",value:"emerald-500",hex:"#10b981",textClass:"text-white"},{name:"Warning",token:"--color-warning",value:"amber-500",hex:"#f59e0b",textClass:"text-white"},{name:"Error",token:"--color-error",value:"rose-600",hex:"#e11d48",textClass:"text-white"}],x=[{name:"Neutral BG",token:"--color-neutral-bg",value:"slate-50",hex:"#f8fafc",textClass:"text-slate-700"},{name:"Surface",token:"--color-surface",value:"white",hex:"#ffffff",textClass:"text-slate-700"},{name:"On Surface",token:"--color-on-surface",value:"slate-800",hex:"#1e293b",textClass:"text-white"},{name:"Text Muted",token:"--color-text-muted",value:"slate-400",hex:"#94a3b8",textClass:"text-white"},{name:"Border Light",token:"--color-border-light",value:"slate-200",hex:"#e2e8f0",textClass:"text-slate-700"}],p=[{name:"Dark BG",token:"--color-dark-bg",value:"—",hex:"#0f172a",textClass:"text-white"},{name:"Dark Surface",token:"--color-dark-surface",value:"—",hex:"#1e293b",textClass:"text-white"},{name:"Dark Border",token:"--color-dark-border",value:"—",hex:"#334155",textClass:"text-white"},{name:"Dark Text",token:"--color-dark-text",value:"—",hex:"#f1f5f9",textClass:"text-slate-800"},{name:"Dark Muted",token:"--color-dark-muted",value:"—",hex:"#94a3b8",textClass:"text-white"}],u=[{name:"Sans (中文字体)",token:"--font-sans",fontFamily:"Noto Sans SC, Inter",fallback:"ui-sans-serif, system-ui"},{name:"Manrope (数字/英文)",token:"--font-manrope",fontFamily:"Manrope, Noto Sans SC",fallback:"sans-serif"},{name:"Inter (英文/数字)",token:"--font-inter",fontFamily:"Inter",fallback:"ui-sans-serif, system-ui"}],v=[{name:"小圆角",class:"rounded-lg",value:"8px"},{name:"中圆角",class:"rounded-xl",value:"12px"},{name:"大圆角",class:"rounded-2xl",value:"16px"},{name:"全圆角",class:"rounded-full",value:"9999px"}],f=[{name:"卡片阴影",class:"shadow-sm",value:"0 1px 2px 0 rgb(0 0 0 / 0.05)"},{name:"升起阴影",class:"shadow-md",value:"0 4px 6px -1px rgb(0 0 0 / 0.1)"},{name:"弹窗阴影",class:"shadow-lg",value:"0 10px 15px -3px rgb(0 0 0 / 0.1)"},{name:"下拉阴影",class:"shadow-xl",value:"0 20px 25px -5px rgb(0 0 0 / 0.1)"}],h=[{name:"XS",class:"p-1",value:"4px"},{name:"SM",class:"p-2",value:"8px"},{name:"MD",class:"p-4",value:"16px"},{name:"LG",class:"p-6",value:"24px"},{name:"XL",class:"p-8",value:"32px"},{name:"2XL",class:"p-10",value:"40px"}],b=[{name:"快速",class:"duration-150",value:"150ms",description:"悬浮、点击反馈"},{name:"标准",class:"duration-200",value:"200ms",description:"按钮、卡片过渡"},{name:"中速",class:"duration-300",value:"300ms",description:"弹窗、面板展开"},{name:"慢速",class:"duration-500",value:"500ms",description:"页面切换"}];function l({name:s,token:o,hex:n,textClass:g}){return e.jsxs("div",{className:"flex items-center gap-3 p-3 bg-surface rounded-xl border border-border-light",children:[e.jsx("div",{className:"w-12 h-12 rounded-xl shrink-0 border border-border-light",style:{backgroundColor:n}}),e.jsxs("div",{className:"min-w-0 flex-1",children:[e.jsx("div",{className:"text-sm font-semibold text-on-surface",children:s}),e.jsx("div",{className:"text-xs text-text-muted font-mono mt-0.5",children:o}),e.jsxs("div",{className:"text-xs text-text-muted mt-0.5",children:[n,e.jsx("span",{className:"ml-2 opacity-60",children:o.replace("--color-","")})]})]})]})}function t({children:s}){return e.jsx("h2",{className:"text-lg font-bold text-on-surface mb-4 flex items-center gap-2",children:s})}function r(){return e.jsx("div",{className:"border-t border-border-light my-8"})}const a={render:()=>e.jsxs("div",{className:"max-w-4xl mx-auto space-y-8",children:[e.jsxs("div",{className:"mb-6",children:[e.jsx("h1",{className:"text-2xl font-800 text-on-surface",style:{fontFamily:"var(--font-manrope)"},children:"🎨 设计 Token"}),e.jsxs("p",{className:"text-sm text-text-muted mt-1",children:["基于 Tailwind v4 ",e.jsx("code",{className:"text-xs bg-slate-100 px-1.5 py-0.5 rounded",children:"@theme"})," 指令定义的设计变量"]})]}),e.jsxs("section",{children:[e.jsx(t,{children:"🎯 品牌色板"}),e.jsx("div",{className:"grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3",children:m.map(s=>e.jsx(l,{...s},s.name))})]}),e.jsx(r,{}),e.jsxs("section",{children:[e.jsx(t,{children:"🧊 表层色板"}),e.jsx("div",{className:"grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3",children:x.map(s=>e.jsx(l,{...s},s.name))})]}),e.jsx(r,{}),e.jsxs("section",{children:[e.jsx(t,{children:"🌙 暗黑模式"}),e.jsxs("p",{className:"text-sm text-text-muted mb-4",children:["通过给父容器添加 ",e.jsx("code",{className:"text-xs bg-slate-100 px-1.5 py-0.5 rounded",children:".dark"})," 类切换。"]}),e.jsx("div",{className:"grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3",children:p.map(s=>e.jsx(l,{...s},s.name))}),e.jsxs("div",{className:"mt-4 p-6 rounded-2xl",style:{backgroundColor:"#0f172a"},children:[e.jsx("p",{className:"text-sm text-white/80 mb-3",children:"暗黑模式预览"}),e.jsxs("div",{className:"flex gap-3",children:[e.jsx("button",{className:"px-4 py-2 rounded-xl text-sm font-medium bg-[#0ea5e9] text-white",children:"Primary"}),e.jsx("button",{className:"px-4 py-2 rounded-xl text-sm font-medium",style:{backgroundColor:"#1e293b",color:"#f1f5f9",border:"1px solid #334155"},children:"Outline"})]})]})]}),e.jsx(r,{}),e.jsxs("section",{children:[e.jsx(t,{children:"🔤 字体体系"}),e.jsx("div",{className:"space-y-4",children:u.map(s=>e.jsxs("div",{className:"p-4 bg-surface rounded-xl border border-border-light",children:[e.jsxs("div",{className:"flex items-center justify-between mb-2",children:[e.jsx("span",{className:"text-sm font-semibold text-on-surface",children:s.name}),e.jsx("span",{className:"text-xs text-text-muted font-mono",children:s.token})]}),e.jsx("p",{className:"text-xl text-on-surface",style:{fontFamily:`var(${s.token})`},children:"AI 数智名片 ABC 123"}),e.jsxs("p",{className:"text-xs text-text-muted mt-1",children:[s.fontFamily,", ",s.fallback]})]},s.name))})]}),e.jsx(r,{}),e.jsxs("section",{children:[e.jsx(t,{children:"🔲 圆角规范"}),e.jsx("div",{className:"flex flex-wrap gap-4",children:v.map(s=>e.jsxs("div",{className:"flex flex-col items-center gap-2",children:[e.jsx("div",{className:`w-16 h-16 bg-primary/20 border-2 border-primary ${s.class}`}),e.jsx("span",{className:"text-xs font-medium text-on-surface",children:s.name}),e.jsx("span",{className:"text-xs text-text-muted font-mono",children:s.value}),e.jsx("span",{className:"text-xs text-text-muted font-mono",children:s.class})]},s.name))})]}),e.jsx(r,{}),e.jsxs("section",{children:[e.jsx(t,{children:"👤 阴影层级"}),e.jsx("div",{className:"grid grid-cols-2 sm:grid-cols-4 gap-4",children:f.map(s=>e.jsxs("div",{className:`p-4 bg-surface rounded-xl border border-border-light ${s.class}`,children:[e.jsx("div",{className:"text-sm font-semibold text-on-surface mb-1",children:s.name}),e.jsx("div",{className:"text-xs text-text-muted font-mono",children:s.class}),e.jsx("div",{className:"text-xs text-text-muted mt-1 break-all",children:s.value})]},s.name))})]}),e.jsx(r,{}),e.jsxs("section",{children:[e.jsx(t,{children:"📐 间距比例"}),e.jsx("div",{className:"space-y-3",children:h.map(s=>e.jsxs("div",{className:"flex items-center gap-4 p-3 bg-surface rounded-xl border border-border-light",children:[e.jsx("span",{className:"text-sm font-medium text-on-surface w-12 shrink-0",children:s.name}),e.jsx("div",{className:"h-8 bg-primary/30 rounded-lg border border-primary/50",style:{width:s.value}}),e.jsx("span",{className:"text-xs text-text-muted font-mono ml-auto",children:s.value}),e.jsx("span",{className:"text-xs text-text-muted font-mono",children:s.class})]},s.name))})]}),e.jsx(r,{}),e.jsxs("section",{children:[e.jsx(t,{children:"⚡ 动画时长"}),e.jsx("div",{className:"grid grid-cols-2 sm:grid-cols-4 gap-4",children:b.map(s=>e.jsxs("div",{className:"p-4 bg-surface rounded-xl border border-border-light text-center",children:[e.jsx("div",{className:"text-sm font-semibold text-on-surface mb-1",children:s.name}),e.jsx("div",{className:"text-xs text-text-muted font-mono mb-2",children:s.value}),e.jsx("div",{className:"w-10 h-10 mx-auto bg-primary rounded-lg animate-pulse"}),e.jsx("p",{className:"text-xs text-text-muted mt-2",children:s.description})]},s.name))})]}),e.jsx(r,{}),e.jsxs("section",{children:[e.jsx(t,{children:"📖 使用方式"}),e.jsx("div",{className:"bg-slate-900 rounded-2xl p-5 overflow-x-auto",children:e.jsx("pre",{className:"text-sm text-slate-200 font-mono leading-relaxed",children:e.jsx("code",{children:`/* 在 Tailwind CSS 中使用 */
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
)} />`})})})]}),e.jsx("div",{className:"h-8"})]}),parameters:{layout:"padded",docs:{description:{story:"完整的设计 Token 展示，涵盖所有色板、字体、圆角、阴影、间距和动画规范。"}}}};var d,i,c;a.parameters={...a.parameters,docs:{...(d=a.parameters)==null?void 0:d.docs,source:{originalSource:`{
  render: () => <div className="max-w-4xl mx-auto space-y-8">\r
      {/* Page header */}\r
      <div className="mb-6">\r
        <h1 className="text-2xl font-800 text-on-surface" style={{
        fontFamily: 'var(--font-manrope)'
      }}>\r
          🎨 设计 Token\r
        </h1>\r
        <p className="text-sm text-text-muted mt-1">\r
          基于 Tailwind v4 <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">@theme</code> 指令定义的设计变量\r
        </p>\r
      </div>\r
\r
      {/* ================================================================ */}\r
      {/* Brand Colors */}\r
      {/* ================================================================ */}\r
      <section>\r
        <SectionTitle>🎯 品牌色板</SectionTitle>\r
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">\r
          {brandColors.map(c => <ColorSwatch key={c.name} {...c} />)}\r
        </div>\r
      </section>\r
\r
      <Divider />\r
\r
      {/* ================================================================ */}\r
      {/* Surface Colors */}\r
      {/* ================================================================ */}\r
      <section>\r
        <SectionTitle>🧊 表层色板</SectionTitle>\r
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">\r
          {surfaceColors.map(c => <ColorSwatch key={c.name} {...c} />)}\r
        </div>\r
      </section>\r
\r
      <Divider />\r
\r
      {/* ================================================================ */}\r
      {/* Dark Mode */}\r
      {/* ================================================================ */}\r
      <section>\r
        <SectionTitle>🌙 暗黑模式</SectionTitle>\r
        <p className="text-sm text-text-muted mb-4">\r
          通过给父容器添加 <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">.dark</code> 类切换。\r
        </p>\r
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">\r
          {darkColors.map(c => <ColorSwatch key={c.name} {...c} />)}\r
        </div>\r
\r
        {/* Dark mode preview */}\r
        <div className="mt-4 p-6 rounded-2xl" style={{
        backgroundColor: '#0f172a'
      }}>\r
          <p className="text-sm text-white/80 mb-3">暗黑模式预览</p>\r
          <div className="flex gap-3">\r
            <button className="px-4 py-2 rounded-xl text-sm font-medium bg-[#0ea5e9] text-white">\r
              Primary\r
            </button>\r
            <button className="px-4 py-2 rounded-xl text-sm font-medium" style={{
            backgroundColor: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155'
          }}>\r
              Outline\r
            </button>\r
          </div>\r
        </div>\r
      </section>\r
\r
      <Divider />\r
\r
      {/* ================================================================ */}\r
      {/* Typography */}\r
      {/* ================================================================ */}\r
      <section>\r
        <SectionTitle>🔤 字体体系</SectionTitle>\r
        <div className="space-y-4">\r
          {fontTokens.map(font => <div key={font.name} className="p-4 bg-surface rounded-xl border border-border-light">\r
              <div className="flex items-center justify-between mb-2">\r
                <span className="text-sm font-semibold text-on-surface">{font.name}</span>\r
                <span className="text-xs text-text-muted font-mono">{font.token}</span>\r
              </div>\r
              <p className="text-xl text-on-surface" style={{
            fontFamily: \`var(\${font.token})\`
          }}>\r
                AI 数智名片 ABC 123\r
              </p>\r
              <p className="text-xs text-text-muted mt-1">\r
                {font.fontFamily}, {font.fallback}\r
              </p>\r
            </div>)}\r
        </div>\r
      </section>\r
\r
      <Divider />\r
\r
      {/* ================================================================ */}\r
      {/* Border Radius */}\r
      {/* ================================================================ */}\r
      <section>\r
        <SectionTitle>🔲 圆角规范</SectionTitle>\r
        <div className="flex flex-wrap gap-4">\r
          {radiusTokens.map(r => <div key={r.name} className="flex flex-col items-center gap-2">\r
              <div className={\`w-16 h-16 bg-primary/20 border-2 border-primary \${r.class}\`} />\r
              <span className="text-xs font-medium text-on-surface">{r.name}</span>\r
              <span className="text-xs text-text-muted font-mono">{r.value}</span>\r
              <span className="text-xs text-text-muted font-mono">{r.class}</span>\r
            </div>)}\r
        </div>\r
      </section>\r
\r
      <Divider />\r
\r
      {/* ================================================================ */}\r
      {/* Shadows */}\r
      {/* ================================================================ */}\r
      <section>\r
        <SectionTitle>👤 阴影层级</SectionTitle>\r
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">\r
          {shadowTokens.map(s => <div key={s.name} className={\`p-4 bg-surface rounded-xl border border-border-light \${s.class}\`}>\r
              <div className="text-sm font-semibold text-on-surface mb-1">{s.name}</div>\r
              <div className="text-xs text-text-muted font-mono">{s.class}</div>\r
              <div className="text-xs text-text-muted mt-1 break-all">{s.value}</div>\r
            </div>)}\r
        </div>\r
      </section>\r
\r
      <Divider />\r
\r
      {/* ================================================================ */}\r
      {/* Spacing */}\r
      {/* ================================================================ */}\r
      <section>\r
        <SectionTitle>📐 间距比例</SectionTitle>\r
        <div className="space-y-3">\r
          {spacingTokens.map(s => <div key={s.name} className="flex items-center gap-4 p-3 bg-surface rounded-xl border border-border-light">\r
              <span className="text-sm font-medium text-on-surface w-12 shrink-0">{s.name}</span>\r
              <div className="h-8 bg-primary/30 rounded-lg border border-primary/50" style={{
            width: s.value
          }} />\r
              <span className="text-xs text-text-muted font-mono ml-auto">{s.value}</span>\r
              <span className="text-xs text-text-muted font-mono">{s.class}</span>\r
            </div>)}\r
        </div>\r
      </section>\r
\r
      <Divider />\r
\r
      {/* ================================================================ */}\r
      {/* Animation */}\r
      {/* ================================================================ */}\r
      <section>\r
        <SectionTitle>⚡ 动画时长</SectionTitle>\r
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">\r
          {animationTokens.map(a => <div key={a.name} className="p-4 bg-surface rounded-xl border border-border-light text-center">\r
              <div className="text-sm font-semibold text-on-surface mb-1">{a.name}</div>\r
              <div className="text-xs text-text-muted font-mono mb-2">{a.value}</div>\r
              <div className="w-10 h-10 mx-auto bg-primary rounded-lg animate-pulse" />\r
              <p className="text-xs text-text-muted mt-2">{a.description}</p>\r
            </div>)}\r
        </div>\r
      </section>\r
\r
      <Divider />\r
\r
      {/* ================================================================ */}\r
      {/* Usage */}\r
      {/* ================================================================ */}\r
      <section>\r
        <SectionTitle>📖 使用方式</SectionTitle>\r
        <div className="bg-slate-900 rounded-2xl p-5 overflow-x-auto">\r
          <pre className="text-sm text-slate-200 font-mono leading-relaxed">\r
            <code>{\`/* 在 Tailwind CSS 中使用 */
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
)} />\`}</code>\r
          </pre>\r
        </div>\r
      </section>\r
\r
      {/* Footer spacer */}\r
      <div className="h-8" />\r
    </div>,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story: '完整的设计 Token 展示，涵盖所有色板、字体、圆角、阴影、间距和动画规范。'
      }
    }
  }
}`,...(c=(i=a.parameters)==null?void 0:i.docs)==null?void 0:c.source}}};const k=["All"];export{a as All,k as __namedExportsOrder,y as default};
