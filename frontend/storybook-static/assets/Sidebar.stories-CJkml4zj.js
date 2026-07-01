import{j as e}from"./iframe-D0-E4Z0o.js";import{S as a}from"./Sidebar-C4SHiSG8.js";import"./preload-helper-Dp1pzeXC.js";import"./sparkles-IPsRl5Xk.js";import"./createLucideIcon-CW88hA_D.js";const v={title:"Components/Sidebar",component:a,parameters:{layout:"fullscreen",docs:{description:{component:"侧边导航栏组件。支持展开/收起切换，含品牌 Logo、导航菜单和收起按钮。"}}}},r={render:()=>e.jsxs("div",{className:"flex h-screen",children:[e.jsx(a,{}),e.jsxs("div",{className:"flex-1 p-6 bg-neutral-bg",children:[e.jsx("h2",{className:"text-lg font-bold text-on-surface",children:"主内容区域"}),e.jsx("p",{className:"text-sm text-text-muted mt-2",children:"侧边栏处于展开状态，点击底部箭头可收起。"})]})]})},s={render:()=>e.jsxs("div",{className:"flex h-screen",children:[e.jsx(a,{}),e.jsxs("main",{className:"flex-1 flex flex-col min-w-0",children:[e.jsx("header",{className:"sticky top-0 z-10 bg-white/80 backdrop-blur-xl border-b border-border-light",children:e.jsx("div",{className:"max-w-5xl mx-auto px-6 py-3 flex items-center justify-between",children:e.jsx("h1",{className:"text-base font-bold text-on-surface",children:"仪表盘"})})}),e.jsx("div",{className:"flex-1 max-w-5xl mx-auto w-full px-6 py-6",children:e.jsx("div",{className:"grid grid-cols-3 gap-4",children:[1,2,3].map(b=>e.jsxs("div",{className:"bg-surface rounded-2xl border border-border-light p-5",children:[e.jsx("div",{className:"w-10 h-10 rounded-xl bg-primary/10 mb-3"}),e.jsx("div",{className:"h-4 w-24 bg-slate-200 rounded mb-2"}),e.jsx("div",{className:"h-3 w-32 bg-slate-100 rounded"})]},b))})})]})]})};var d,t,l,n,o;r.parameters={...r.parameters,docs:{...(d=r.parameters)==null?void 0:d.docs,source:{originalSource:`{
  render: () => <div className="flex h-screen">\r
      <Sidebar />\r
      <div className="flex-1 p-6 bg-neutral-bg">\r
        <h2 className="text-lg font-bold text-on-surface">主内容区域</h2>\r
        <p className="text-sm text-text-muted mt-2">侧边栏处于展开状态，点击底部箭头可收起。</p>\r
      </div>\r
    </div>
}`,...(l=(t=r.parameters)==null?void 0:t.docs)==null?void 0:l.source},description:{story:"展开状态 — 默认宽度 224px",...(o=(n=r.parameters)==null?void 0:n.docs)==null?void 0:o.description}}};var c,i,m,x,p;s.parameters={...s.parameters,docs:{...(c=s.parameters)==null?void 0:c.docs,source:{originalSource:`{
  render: () => <div className="flex h-screen">\r
      <Sidebar />\r
      <main className="flex-1 flex flex-col min-w-0">\r
        <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-xl border-b border-border-light">\r
          <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">\r
            <h1 className="text-base font-bold text-on-surface">仪表盘</h1>\r
          </div>\r
        </header>\r
        <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-6">\r
          <div className="grid grid-cols-3 gap-4">\r
            {[1, 2, 3].map(i => <div key={i} className="bg-surface rounded-2xl border border-border-light p-5">\r
                <div className="w-10 h-10 rounded-xl bg-primary/10 mb-3" />\r
                <div className="h-4 w-24 bg-slate-200 rounded mb-2" />\r
                <div className="h-3 w-32 bg-slate-100 rounded" />\r
              </div>)}\r
          </div>\r
        </div>\r
      </main>\r
    </div>
}`,...(m=(i=s.parameters)==null?void 0:i.docs)==null?void 0:m.source},description:{story:"嵌入 Dashboard 布局",...(p=(x=s.parameters)==null?void 0:x.docs)==null?void 0:p.description}}};const j=["Expanded","InDashboard"];export{r as Expanded,s as InDashboard,j as __namedExportsOrder,v as default};
